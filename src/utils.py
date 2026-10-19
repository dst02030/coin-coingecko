"""Configuration, Discord delivery and transactional PostgreSQL access."""
import logging
import re

import pandas as pd
import requests
import yaml
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from sqlalchemy.dialects.postgresql import insert

logger = logging.getLogger(__name__)


def load_config(*file_names):
    config = {}
    for file_name in file_names:
        with open(file_name, encoding="utf-8") as stream:
            config.update(yaml.safe_load(stream) or {})
    return config


# Keep existing notebook imports working without requiring Jinja2.
get_jinja_yaml_conf = load_config


def send_message_to_discord(url, msg):
    response = requests.post(url, json={"content": msg}, timeout=30)
    if not response.ok:
        # Do not include the response/request URL: it contains the webhook token.
        raise RuntimeError(f"Discord delivery failed (HTTP {response.status_code})")
    logger.info("Discord message delivered")


def create_db_engine(engine_info):
    url = URL.create(
        drivername=engine_info["DB_TYPE"], username=engine_info["DB_USER"],
        password=engine_info["DB_PASSWORD"], host=engine_info["DB_HOST"],
        port=int(engine_info["DB_PORT"]), database=engine_info["DB_NAME"],
    )
    return create_engine(url, client_encoding="utf8")


def _identifier(name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid SQL identifier: {name!r}")
    return f'"{name}"'


def _columns(columns):
    if isinstance(columns, str):
        columns = [columns]
    return ", ".join(_identifier(c) for c in columns) if columns else "*"


class Postgres_connect:
    def __init__(self, engine):
        self.engine = engine

    def get_data(self, schema_name, table_name, columns=None, where=None,
                 where_operator="AND", additional_sql="", is_distinct=False,
                 orderby_cols=None):
        sql = (f"SELECT {'DISTINCT ' if is_distinct else ''}{_columns(columns)} "
               f"FROM {_identifier(schema_name)}.{_identifier(table_name)} "
               f"{self._make_where(where, where_operator)} {additional_sql}")
        if orderby_cols:
            sql += f" ORDER BY {_columns(orderby_cols)}"
        return pd.read_sql(sql, con=self.engine)

    def get_maxmin_col(self, schema_name, table_name, column, where=None,
                       where_operator="AND", additional_sql="", is_max=True, is_min=True):
        if not (is_max or is_min):
            raise ValueError("Select at least one of is_max or is_min")
        values = [f"{op}({_identifier(column)})" for op, enabled
                  in [("MAX", is_max), ("MIN", is_min)] if enabled]
        sql = (f"SELECT {', '.join(values)} FROM {_identifier(schema_name)}."
               f"{_identifier(table_name)} {self._make_where(where, where_operator)} {additional_sql}")
        return pd.read_sql(sql, con=self.engine).to_numpy().ravel()

    def get_count(self, schema_name, table_name, where=None,
                  where_operator="AND", additional_sql=""):
        sql = (f"SELECT COUNT(*) FROM {_identifier(schema_name)}.{_identifier(table_name)} "
               f"{self._make_where(where, where_operator)} {additional_sql}")
        return int(pd.read_sql(sql, con=self.engine).iloc[0, 0])

    def insert_df(self, data, schema_name, table_name):
        if data.empty:
            return 0
        with self.engine.begin() as connection:
            return data.to_sql(table_name, schema=schema_name, con=connection,
                               if_exists="append", index=False, chunksize=1000)

    def upsert(self, data, schema_name, table_name, del_rows=1000):
        """Insert/update rows atomically; never delete committed rows first."""
        if del_rows < 1:
            raise ValueError("Chunk size must be positive")
        if data.empty:
            return 0
        with self.engine.begin() as connection:
            primary_keys = inspect(connection).get_pk_constraint(
                table_name, schema=schema_name)["constrained_columns"]
            frame = data.drop_duplicates(primary_keys, keep="last") if primary_keys else data

            def write_chunk(table, conn, keys, data_iter):
                rows = [dict(zip(keys, row)) for row in data_iter]
                statement = insert(table.table).values(rows)
                if primary_keys:
                    updates = {key: statement.excluded[key] for key in keys
                               if key not in primary_keys}
                    if updates:
                        statement = statement.on_conflict_do_update(
                            index_elements=primary_keys, set_=updates)
                    else:
                        statement = statement.on_conflict_do_nothing(index_elements=primary_keys)
                return conn.execute(statement).rowcount

            return frame.to_sql(table_name, schema=schema_name, con=connection,
                                index=False, if_exists="append", chunksize=del_rows,
                                method=write_chunk)

    def ext_notin_db(self, data, schema_name, table_name, subset=None):
        subset = [subset] if isinstance(subset, str) else list(subset or data.columns)
        existing = self.get_data(schema_name, table_name, columns=subset, is_distinct=True)
        return data.merge(existing, how="left", on=subset, indicator=True).query(
            "_merge == 'left_only'").drop(columns="_merge")

    def get_engine(self):
        return self.engine

    @staticmethod
    def _make_where(where, where_operator="AND"):
        if where_operator not in {"AND", "OR"}:
            raise ValueError("where_operator must be AND or OR")
        clauses = [where] if isinstance(where, str) else where
        return f"WHERE {f' {where_operator} '.join(clauses)}" if clauses else ""


def load_credentials(file_name):
    """Source the same trusted local shell file used by run.sh."""
    import json
    import os
    import subprocess
    import sys

    script = 'set -ae; source "$1"; "$2" -c \'import json, os; print(json.dumps(dict(os.environ)))\''
    result = subprocess.run(
        ["bash", "-c", script, "load-credentials", str(file_name), sys.executable],
        check=True, capture_output=True, text=True,
    )
    os.environ.update(json.loads(result.stdout))
