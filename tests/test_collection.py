"""Offline regression checks: no production HTTP or database access."""
import copy
import importlib.util
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import Mock, patch

import pandas as pd
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from src.api import Coingecko
from src import processing
from src.utils import Postgres_connect, create_db_engine, load_config, send_message_to_discord

ROOT = Path(__file__).resolve().parents[1]


def response(status=200, payload=None):
    res = Mock(status_code=status, ok=status < 400)
    res.json.return_value = payload
    if status >= 400:
        res.raise_for_status.side_effect = requests.HTTPError(str(status))
    return res


class ApiTests(unittest.TestCase):
    @patch('src.api.requests.get')
    def test_auth_and_timeout_and_encoded_params(self, get):
        get.return_value = response(payload=[])
        Coingecko(auth_key='test').get_api_data('coins/list', {'query': 'a & b'})
        self.assertEqual(get.call_args.kwargs['headers'], {'x-cg-pro-api-key': 'test'})
        self.assertEqual(get.call_args.kwargs['params'], {'query': 'a & b'})
        self.assertEqual(get.call_args.kwargs['timeout'], 30)

    @patch('src.api.time.sleep')
    @patch('src.api.requests.get')
    def test_server_error_and_rate_limit_then_success(self, get, sleep):
        get.side_effect = [response(500), response(429), response(payload=[])]
        Coingecko().get_api_data(max_retries=3, sleep=0)
        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch('src.api.requests.get')
    def test_client_error_is_not_retried(self, get):
        get.return_value = response(401)
        with self.assertRaises(requests.HTTPError):
            Coingecko().get_api_data(max_retries=3)
        self.assertEqual(get.call_count, 1)

    @patch('src.api.time.sleep')
    @patch('src.api.requests.get', side_effect=requests.Timeout('test'))
    def test_connection_exhaustion_keeps_original_exception(self, get, sleep):
        with self.assertRaises(requests.Timeout):
            Coingecko().get_api_data(max_retries=2, sleep=0)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(sleep.call_count, 1)

    @patch('src.api.requests.get')
    def test_http_exhaustion_raises_http_error(self, get):
        get.return_value = response(503)
        with self.assertRaises(requests.HTTPError):
            Coingecko().get_api_data(max_retries=1)

    def test_page_params_unchanged_and_timestamp_shared(self):
        api = Coingecko()
        api.get_api_data = Mock(side_effect=[response(payload=[{'id': 1}]),
                                             response(payload=[{'id': 2}])])
        params = {'per_page': 1}
        result = api.get_page_data(params=params, end_pages=2)
        self.assertEqual(params, {'per_page': 1})
        self.assertEqual(result['id'].tolist(), [1, 2])
        self.assertEqual(result['_ts'].nunique(), 1)
        pages = [call.args[1]['page'] for call in api.get_api_data.call_args_list]
        self.assertEqual(pages, [1, 2])

    def test_collection_timestamp_is_created_on_each_call(self):
        api = Coingecko()
        api.get_api_data = Mock(return_value=response(payload=[{'id': 1}]))
        with patch('src.api.datetime') as clock:
            clock.now.return_value.astimezone.side_effect = ['first', 'second']
            self.assertEqual(api.get_data('x')['_ts'].iloc[0], 'first')
            self.assertEqual(api.get_data('x')['_ts'].iloc[0], 'second')

    def test_short_page_stops_and_empty_response_supported(self):
        api = Coingecko()
        api.get_api_data = Mock(return_value=response(payload=[{'id': 1}]))
        self.assertEqual(len(api.get_page_data(params={'per_page': 250})), 1)
        self.assertEqual(api.get_api_data.call_count, 1)
        api.get_api_data.return_value = response(payload=[])
        self.assertTrue(api.get_page_data().empty)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        with self.engine.begin() as conn:
            conn.execute(text('CREATE TABLE sample (id TEXT PRIMARY KEY, value INTEGER NOT NULL)'))
            conn.execute(text("INSERT INTO sample VALUES ('original', 1)"))
        self.db = Postgres_connect(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def rows(self):
        return self.db.get_data('main', 'sample', orderby_cols='id').to_dict('records')

    def test_update_and_insert_without_deleting_rows(self):
        self.db.upsert(pd.DataFrame({'id': ['original', 'new'], 'value': [2, 3]}), 'main', 'sample')
        self.assertEqual(self.rows(), [{'id': 'new', 'value': 3}, {'id': 'original', 'value': 2}])

    def test_later_chunk_failure_rolls_back_all_changes(self):
        data = pd.DataFrame({'id': ['original', 'invalid'], 'value': [9, None]})
        with self.assertRaises(IntegrityError):
            self.db.upsert(data, 'main', 'sample', del_rows=1)
        self.assertEqual(self.rows(), [{'id': 'original', 'value': 1}])

    def test_duplicate_incoming_keys_keep_last(self):
        data = pd.DataFrame({'id': ['original', 'original'], 'value': [2, 3]})
        self.db.upsert(data, 'main', 'sample')
        self.assertEqual(self.rows(), [{'id': 'original', 'value': 3}])

    def test_insert_failure_rolls_back_earlier_chunk(self):
        data = pd.DataFrame({'id': ['new'] * 1001, 'value': [1] * 1001})
        with self.assertRaises(IntegrityError):
            self.db.insert_df(data, 'main', 'sample')
        self.assertEqual(self.rows(), [{'id': 'original', 'value': 1}])

    def test_empty_frame_is_noop(self):
        self.assertEqual(self.db.upsert(pd.DataFrame(), 'main', 'sample'), 0)
        self.assertEqual(self.db.insert_df(pd.DataFrame(), 'main', 'sample'), 0)

    @patch('src.utils.create_engine')
    def test_db_password_special_characters_preserved(self, create):
        values = dict(DB_TYPE='postgresql+psycopg2', DB_USER='user', DB_PASSWORD='a/@:%',
                      DB_HOST='localhost', DB_PORT='5432', DB_NAME='db')
        create_db_engine(values)
        url = create.call_args.args[0]
        self.assertEqual(url.password, values['DB_PASSWORD'])
        self.assertEqual(url.drivername, values['DB_TYPE'])


class ProcessingTests(unittest.TestCase):
    def markets(self, count):
        return pd.DataFrame({'id': [str(i) for i in range(count)],
                             'roi': [None] * count, 'total_volume': range(1, count + 1),
                             'market_cap': [10] * count, 'market_cap_rank': range(1, count + 1)})

    def test_deduplicate_before_ranking_and_zero_cap_not_infinite(self):
        data = self.markets(2)
        data.loc[0, 'market_cap'] = 0
        data = pd.concat([data, data.iloc[[1]]])
        result = processing.preprocessing_coins_markets(data)
        self.assertEqual(len(result), 2)
        self.assertTrue(pd.isna(result.set_index('id').loc['0', 'vol_cap_ratio']))
        self.assertEqual(result.set_index('id').loc['0', 'volume_rank'], 2)

    @patch.dict(os.environ, {'webhook_url': 'https://example.invalid'})
    @patch('src.processing.send_message_to_discord')
    def test_webhook_keeps_partial_final_chunk_without_refetch(self, send):
        data = processing.preprocessing_coins_markets(self.markets(55))
        api = Mock()
        conf = {'rename': {'index': 'rank', 'id': 'id'}}
        processing.webhook_coins_markets(api, conf,
            {'total_rows': 55, 'print_rows': 10, 'space_len': 5}, data=data)
        api.get_page_data.assert_not_called()
        self.assertEqual(send.call_count, 7)  # Heading plus six chunks.
        self.assertIn('55', send.call_args.args[1])

    @patch('src.processing.send_message_to_discord')
    def test_empty_market_response_does_not_send(self, send):
        frame = processing.preprocessing_coins_markets(pd.DataFrame())
        processing.webhook_coins_markets(Mock(), {},
            {'total_rows': 50, 'print_rows': 10}, data=frame)
        send.assert_not_called()

    def test_trending_does_not_mutate_response(self):
        payload = {'coins': [{'item': {'id': 'one', 'data': {'content': {'x': 1}}}}]}
        original = copy.deepcopy(payload)
        api = Mock()
        api.get_api_data.return_value.json.return_value = payload
        db = Mock()
        processing.upload_trending(db, api, {'url': 'search/trending', 'data': {
            'coins': {'json_cols': ['content'], 'schema_name': 'x', 'table_name': 'y'}}})
        self.assertEqual(payload, original)
        self.assertEqual(db.insert_df.call_args.args[0]['content'].iloc[0], '{"x": 1}')

    def test_global_nested_response(self):
        api = Coingecko()
        api.get_api_data = Mock(return_value=response(payload={'data': {
            'active_cryptocurrencies': 5, 'market_cap_percentage': {'btc': 1},
            'total_market_cap': {'usd': 2}, 'total_volume': {'usd': 3}}}))
        db = Mock()
        processing.upload_global(db, api, {'url': 'global', 'schema_name': 'x', 'table_name': 'y'})
        self.assertEqual(db.insert_df.call_args.args[0]['active_cryptocurrencies'].iloc[0], 5)

    def test_companies_normalization(self):
        api = Coingecko()
        api.get_api_data = Mock(return_value=response(payload={
            'total_holdings': 10, 'companies': [{'name': 'a', 'total_holdings': 3},
                                               {'name': 'b', 'total_holdings': 7}]}))
        db = Mock()
        processing.upload_companies_treasury(db, api, {
            'url': 'companies/public_treasury', 'coin_list': ['bitcoin'],
            'rename': {'total_holdings': 'total_companies_holdings'},
            'company_rename': {'total_holdings': 'company_holdings'},
            'schema_name': 'x', 'table_name': 'y'})
        data = db.insert_df.call_args.args[0]
        self.assertEqual(data['company_holdings'].tolist(), [3, 7])
        self.assertEqual(data['total_companies_holdings'].tolist(), [10, 10])

    @patch('src.utils.requests.post')
    def test_discord_failure_is_reported(self, post):
        post.return_value = response(429)
        with self.assertRaises(RuntimeError):
            send_message_to_discord('https://example.invalid', 'test')
        self.assertEqual(post.call_count, 1)
        self.assertEqual(post.call_args.kwargs['timeout'], 30)

    def test_cli_shares_market_data_between_db_and_webhook(self):
        spec = importlib.util.spec_from_file_location('coin_main', ROOT / 'main.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        conf = load_config(ROOT/'conf/data.yml', ROOT/'conf/logging.yml', ROOT/'conf/webhook.yml')
        conf['logging']['file_name'] = str(Path(tempfile.gettempdir()) / 'coin-regression.log')
        with patch.object(module, 'load_config', return_value=conf), \
             patch.object(module, 'create_db_engine') as engine, \
             patch.object(module, 'Coingecko') as api, \
             patch.object(processing, 'upload_coins_markets') as upload, \
             patch.object(processing, 'webhook_coins_markets') as send:
            api.return_value.get_page_data.return_value = self.markets(2)
            module.main(['coins_markets'])
            api.return_value.get_page_data.assert_called_once()
            self.assertIs(upload.call_args.kwargs['data'], send.call_args.kwargs['data'])
            engine.return_value.dispose.assert_called_once()


class ConfigurationTests(unittest.TestCase):
    def test_notebook_credentials_match_shell_quoting_and_expansion(self):
        from src.utils import load_credentials
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=False):
            path = Path(directory) / 'credentials'
            path.write_text("COIN_TEST_A='literal $HOME # value'\n"
                            'COIN_TEST_B="${COIN_TEST_A}/suffix"\n')
            load_credentials(path)
            self.assertEqual(os.environ['COIN_TEST_A'], 'literal $HOME # value')
            self.assertEqual(os.environ['COIN_TEST_B'], 'literal $HOME # value/suffix')

    def test_sql_failure_is_propagated_and_host_is_from_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            fake = path / 'psql'
            fake.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$COIN_TEST_ARGS"\nexit 7\n')
            fake.chmod(0o755)
            env = {**os.environ, 'PATH': f'{path}:' + os.environ['PATH'],
                   'DB_HOST': 'test-host', 'DB_PORT': '1234', 'DB_USER': 'test-user',
                   'DB_NAME': 'test-db', 'DB_PASSWORD': 'dummy-password',
                   'COIN_TEST_ARGS': str(path/'args')}
            result = subprocess.run(['bash', str(ROOT/'src/sql/create_tables.sh')],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 7)
            self.assertIn('--host=test-host', (path/'args').read_text())
            self.assertNotIn('dummy-password', result.stdout + result.stderr)
            self.assertIn('ON_ERROR_STOP=1', (path/'args').read_text())

    def test_runner_respects_conda_path_and_loads_credentials(self):
        with tempfile.TemporaryDirectory(prefix='coin runner ') as directory:
            root = Path(directory)
            (root/'conf').mkdir()
            (root/'conf/credentials').write_text("COIN_TEST_SECRET='dummy'\n")
            runner = root/'run.sh'
            runner.write_text((ROOT/'run.sh').read_text())
            conda = root/'custom conda/etc/profile.d'
            conda.mkdir(parents=True)
            (conda/'conda.sh').write_text(
                'conda() { [ "$1" = activate ] && [ "$2" = test-env ]; }\n')
            executable = root/'python3'
            executable.write_text('#!/bin/bash\n[ "$COIN_TEST_SECRET" = dummy ] || exit 9\n'
                                  'printf "%s\\n" "$@" > "$COIN_TEST_ARGS"\n')
            executable.chmod(0o755)
            env = {**os.environ, 'CONDA_VOLUME': str(root/'custom conda'),
                   'CONDA_ENV': 'test-env', 'PATH': f"{root}:" + os.environ['PATH'],
                   'COIN_TEST_ARGS': str(root/'args')}
            result = subprocess.run(['bash', str(runner), 'coins_list'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root/'args').read_text().splitlines(),
                             [str(root/'main.py'), 'coins_list'])
            self.assertNotIn('dummy', result.stdout + result.stderr)

    def test_missing_cli_argument_fails_before_conda_or_credentials(self):
        result = subprocess.run(['bash', str(ROOT/'run.sh')], capture_output=True, text=True,
                                env={**os.environ, 'CONDA_VOLUME': '/does-not-exist'})
        self.assertEqual(result.returncode, 1)
        self.assertIn('Usage:', result.stderr)
        self.assertNotIn('No such file', result.stderr)


if __name__ == '__main__':
    unittest.main()
