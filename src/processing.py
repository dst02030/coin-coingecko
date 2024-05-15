import json
import logging
import os
import time
import numpy as np
import pandas as pd

from collections import deque
from datetime import datetime, timedelta
from src.utils import send_message_to_discord


logger = logging.getLogger(__name__)


def preprocessing_coins_markets(data):
    data = data.copy()

    data['roi'] = data['roi'].map(lambda x: json.dumps(x) if type(x) is dict else x)
    data['volume_rank'] = data['total_volume'].rank(ascending = False)
    
    data['rank_prop'] = data['market_cap_rank'] / data['volume_rank'] 
    data['vol_cap_ratio'] = data['total_volume'] / data['market_cap'] 

    data.sort_values('vol_cap_ratio', ascending = False, inplace = True)
    data.drop_duplicates('id', keep = 'first', inplace = True)
    return data


def upload_coins_markets(db_conn, api, conf_coins_markets):

    data = api.get_page_data(detail_url = conf_coins_markets['url'], params = conf_coins_markets['params'], 
                               end_pages = conf_coins_markets['max_pages'])
    

    data = preprocessing_coins_markets(data)
    db_conn.insert_df(data, schema_name = conf_coins_markets['schema_name'], table_name = conf_coins_markets['table_name'])
    logger.info('upload coins_markets finished!')
    
    
def webhook_coins_markets(api, conf_coins_markets, conf_webhook):
    data = api.get_page_data(detail_url = conf_coins_markets['url'],
                             params = conf_coins_markets['params'], 
                            end_pages = conf_webhook['total_rows'] // 100 + 1)
    

    data = preprocessing_coins_markets(data)
    
    data_processed = data[[column 
                           for column in data.columns 
                           if column in conf_coins_markets['rename']]
                            ].reset_index(drop = True).round(2).reset_index()
    data_processed['index'] += 1
    data_processed.rename(columns = conf_coins_markets['rename'], inplace = True)

    send_message_to_discord(os.environ['webhook_url'], f"{datetime.now().strftime('%Y년 %m월 %d일 %H시')} 코인 정보")
    for i in range(conf_webhook['total_rows'] // conf_webhook['print_rows']):
    
        msg = [''.join(f"{column}{' '*(conf_webhook['space_len'] - len(str(column)*2))}" for column in data_processed.columns)]
        
        for n, vals in data_processed.iloc[i*conf_webhook['print_rows']:(i+1)*conf_webhook['print_rows']].iterrows():
            msg.append(''.join([f"{str(val)}{' '*(conf_webhook['space_len'] - len(str(val)))}" for val in vals]))
        msg = '\n'.join(msg)
    
        send_message_to_discord(os.environ['webhook_url'], f"```{msg}```")

    logger.info("coins_markets webhook upload finished")


def upload_coin_list(db_conn, api, conf_coins_list):

    data = api.get_data(detail_url= conf_coins_list['url'],
                 params = {'include_platform': 'true'})

    data['platforms'] = data['platforms'].map(lambda x: json.dumps(x) if type(x) is dict else x)
    
    db_conn.upsert(data, schema_name = conf_coins_list['schema_name'], table_name = conf_coins_list['table_name'])
    logger.info('upload coin_list finished!')


def upload_asset_platforms(db_conn, api, conf_asset_pltfm):
    data = api.get_data(detail_url= conf_asset_pltfm['url'])
    db_conn.upsert(data, schema_name = conf_asset_pltfm['schema_name'], table_name = conf_asset_pltfm['table_name'])
    logger.info('upload asset_platforms finished!')

def upload_categories(db_conn, api, conf_categories):
    data = api.get_data(detail_url= conf_categories['url'])
    db_conn.insert_df(data, schema_name = conf_categories['schema_name'], table_name = conf_categories['table_name'])
    logger.info('upload categories finished!')

def upload_categories_list(db_conn, api, conf_categories_list):
    data = api.get_data(detail_url= conf_categories_list['url'])
    db_conn.upsert(data, schema_name = conf_categories_list['schema_name'], table_name = conf_categories_list['table_name'])
    logger.info('upload categories_list finished!')

def upload_exchanges_list(db_conn, api, conf_exchanges_list):
    data = api.get_data(detail_url= conf_exchanges_list['url'])
    db_conn.upsert(data, schema_name = conf_exchanges_list['schema_name'], table_name = conf_exchanges_list['table_name'])
    logger.info('upload exchanges_list finished!')

def upload_exchanges(db_conn, api, conf_exchanges):

    data = api.get_page_data(detail_url = conf_exchanges['url'], params = conf_exchanges['params'], 
                               end_pages = conf_exchanges['max_pages']).drop_duplicates('id')
    
    db_conn.insert_df(data, schema_name = conf_exchanges['schema_name'], table_name = conf_exchanges['table_name'])
    logger.info('upload exchanges finished!')

def upload_derivatives(db_conn, api, conf_derivatives):

    data = api.get_data(detail_url = conf_derivatives['url']).drop_duplicates(['market', 'symbol', 'index_id'])
    
    db_conn.insert_df(data, schema_name = conf_derivatives['schema_name'], table_name = conf_derivatives['table_name'])
    logger.info('upload derivatives finished!')

def upload_derivatives_exchanges(db_conn, api, conf_derivatives_exchanges):

    data = api.get_page_data(detail_url = conf_derivatives_exchanges['url'], params = conf_derivatives_exchanges['params'], end_pages = conf_derivatives_exchanges['max_pages'])
    
    db_conn.insert_df(data, schema_name = conf_derivatives_exchanges['schema_name'], table_name = conf_derivatives_exchanges['table_name'])
    logger.info('upload derivatives_exchanges finished!')

def upload_derivatives_exchanges_list(db_conn, api, conf_derivatives_exchanges_list):

    data = api.get_data(detail_url = conf_derivatives_exchanges_list['url'])
    
    db_conn.upsert(data, schema_name = conf_derivatives_exchanges_list['schema_name'], table_name = conf_derivatives_exchanges_list['table_name'])
    logger.info('upload derivatives_exchanges_list finished!')


def upload_nfts_list(db_conn, api, conf_nfts_list):

    data = api.get_page_data(detail_url = conf_nfts_list['url'], params = conf_nfts_list['params'], 
                               end_pages = conf_nfts_list['max_pages'], sleep = 200).drop_duplicates()
    
    db_conn.upsert(data, schema_name = conf_nfts_list['schema_name'], table_name = conf_nfts_list['table_name'])
    logger.info('upload nfts_list finished!')

def upload_trending(db_conn, api, conf_trending):
    data = json.loads(
    api.get_api_data(conf_trending['url']).text)
    
    for key in conf_trending['data'].keys():
        keys = [key['item'] if 'item' in key else key for key in data[key]]
    
        for idx, _ in enumerate(keys):
            key_data = keys[idx]['data']
            keys[idx].update(key_data)
            del keys[idx]['data']
    
        keys_data = pd.DataFrame(keys)
        keys_data[conf_trending['data'][key]['json_cols']] = keys_data[conf_trending['data'][key]['json_cols']].map(lambda x: json.dumps(x) if type(x) is dict else x)
        keys_data['_ts'] = datetime.astimezone(datetime.now())
        db_conn.insert_df(keys_data, conf_trending['data'][key]['schema_name'], conf_trending['data'][key]['table_name'])
    

def upload_global(db_conn, api, conf_global):

    data = api.get_data(detail_url = conf_global['url'])

    data = pd.DataFrame([data['data']])
    data['_ts'] = datetime.astimezone(datetime.now())
    data['market_cap_percentage'] = data['market_cap_percentage'].map(lambda x: json.dumps(x) if type(x) is dict else x)
    data['total_market_cap'] = data['total_market_cap'].map(lambda x: json.dumps(x) if type(x) is dict else x)
    data['total_volume'] = data['total_volume'].map(lambda x: json.dumps(x) if type(x) is dict else x)
    db_conn.insert_df(data, schema_name = conf_global['schema_name'], table_name = conf_global['table_name'])
    logger.info('upload global finished!')


def upload_companies_treasury(db_conn, api, conf_companies_treasury):
    data = pd.DataFrame()
    for coin in conf_companies_treasury['coin_list']:
        this_data = api.get_data(detail_url= f"{conf_companies_treasury['url']}/{coin}", rename = conf_companies_treasury['rename'])
        this_data['coin_id'] = coin
        this_data = pd.concat([this_data,
        pd.DataFrame(this_data['companies'].tolist()).rename(conf_companies_treasury['company_rename'], axis = 1)], axis = 1)
        this_data.drop('companies', axis = 1, inplace = True)
        data = pd.concat([data, this_data])
    db_conn.insert_df(data, schema_name = conf_companies_treasury['schema_name'], table_name = conf_companies_treasury['table_name'])
    logger.info('upload companies_treasury finished!')