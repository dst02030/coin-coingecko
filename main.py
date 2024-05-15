import logging
import requests
import json
import os
import time
import pandas as pd
import numpy as np

import requests
import sys
from datetime import datetime, timedelta, date
from logging.handlers import TimedRotatingFileHandler

from src.api import Coingecko
from src.utils import get_jinja_yaml_conf, create_db_engine, Postgres_connect, send_message_to_discord
from src.processing import *

def main():
    os.chdir(os.path.dirname(__file__))
    conf = get_jinja_yaml_conf('./conf/webhook.yml', './conf/logging.yml', './conf/data.yml')



    # logger 설정
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=eval(conf['logging']['level']),
        format=conf['logging']['format'],
        handlers = [TimedRotatingFileHandler(filename =  conf['logging']['file_name'],
                                    when=conf['logging']['when'],
                                    interval=conf['logging']['interval'],
                                    backupCount=conf['logging']['backupCount']), logging.StreamHandler()]
                    )



    engine = create_db_engine(os.environ)
    postgres_conn = Postgres_connect(engine)
    gecko_api = Coingecko()
    
    if sys.argv[1] in conf['data']:
        logger.info(f"Run {sys.argv[1]}!")
    
    else:
        raise Exception(f"You entered not allowed run mode. Run modes are: {list(conf['data'].keys())}")
    
    
    if sys.argv[1] == 'coins_markets':
        webhook_coins_markets(gecko_api, conf['data']['coins_markets'], conf['webhook'])
        upload_coins_markets(postgres_conn, gecko_api, conf['data']['coins_markets'])

    elif sys.argv[1] == 'coins_list':
        upload_coin_list(postgres_conn, gecko_api, conf['data']['coins_list'])

    elif sys.argv[1] == 'asset_platforms':
        upload_asset_platforms(postgres_conn, gecko_api, conf['data']['asset_platforms'])

    elif sys.argv[1] == 'categories_list':
        upload_categories_list(postgres_conn, gecko_api, conf['data']['categories_list'])

    elif sys.argv[1] == 'categories':
        upload_categories(postgres_conn, gecko_api, conf['data']['categories'])

    elif sys.argv[1] == 'exchanges_list':
        upload_exchanges_list(postgres_conn, gecko_api, conf['data']['exchanges_list'])

    elif sys.argv[1] == 'exchanges':
        upload_exchanges(postgres_conn, gecko_api, conf['data']['exchanges'])

    elif sys.argv[1] == 'derivatives':
        upload_derivatives(postgres_conn, gecko_api, conf['data']['derivatives'])

    elif sys.argv[1] == 'derivatives_exchanges':
        upload_derivatives_exchanges(postgres_conn, gecko_api, conf['data']['derivatives_exchanges'])

    elif sys.argv[1] == 'derivatives_exchanges_list':
        upload_derivatives_exchanges_list(postgres_conn, gecko_api, conf['data']['derivatives_exchanges_list'])

    elif sys.argv[1] == 'trending':
        upload_trending(postgres_conn, gecko_api, conf['data']['trending'])

    elif sys.argv[1] == 'global': 
        upload_global(postgres_conn, gecko_api, conf['data']['global'])

    elif sys.argv[1] == 'nfts_list':
        upload_nfts_list(postgres_conn, gecko_api, conf['data']['nfts_list'])
    
    elif sys.argv[1] == 'companies_treasury':
        upload_companies_treasury(postgres_conn, gecko_api, conf['data']['companies_treasury'])

        
if __name__ == "__main__":
    main()