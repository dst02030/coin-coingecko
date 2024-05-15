import logging
import json
import requests
import io
import os
import time
import zipfile


import numpy as np
import pandas as pd

from io import BytesIO
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)




class Coingecko:
    def __init__(self, base_url = None, auth_key = None):
        logger.info(f"### Coingecko main api is initialized! ###")
        self.base_url = base_url if base_url else 'https://api.coingecko.com/api/v3'
        self.auth_key = auth_key = None
        self.headers = {'x-cg-pro-api-key': auth_key} if auth_key else None



    def get_api_data(self, detail_url = '', params = {}, max_retries = 30, sleep = 60):
        tries = 0
        
        url = f"{self.base_url}/{detail_url}"
        query_url = "&".join([f"{key}={val}" for key, val in params.items()])
    
        url += f"?{query_url}" if len(query_url) > 0 else ""

        while tries < max_retries:
            tries += 1
            res = requests.get(url, headers = self.headers)
            
            if not res.ok:
                if res.status_code != 429:
                    logger.warning(f"There is some error in {detail_url}, params: {params}")
                    logger.warning(content)
                    res.raise_for_status()

                logger.info(f"Exceeded api call rate limit. API call now tries: {tries}/{max_retries}; sleep {sleep} secs.")
                logger.info(res.text)
                time.sleep(sleep)
                continue
            
            return res

        logger.error(f"Exceeded {max_retries} retries. Please try again.")
        res.raise_for_status()
    
    def get_data(self, detail_url, params = {}, _ts = datetime.astimezone(datetime.now()), rename = None, sleep = 60, max_retries = 30):
        data = pd.DataFrame()
        
        data = pd.DataFrame(json.loads(self.get_api_data(detail_url, params, sleep = sleep, max_retries = max_retries).text
                                      )
                           )
            
        if data.shape[0] == 0:
            return pd.DataFrame()
        
        data['_ts'] = _ts

        if rename:
            data = data.rename(columns = rename)
        
        return data
    
    def get_page_data(self, detail_url = 'coins/markets', start_pages = 1, end_pages = 10, params = {}, rename = None, sleep = 700, max_retries = 3):
        data = pd.DataFrame()
        for page in range(start_pages, end_pages+1):
            logger.info(f"Get data ({page}/{end_pages})...")
            params['page'] = page
            this_data = self.get_data(detail_url, params, rename = rename, sleep = sleep, max_retries = max_retries)
            if this_data.shape[0] == 0:
                logger.warning(f"There is no data in {page} page. Skip residual pages.")
                break
            data = pd.concat([data, this_data])
        return data
    
  