"""CoinGecko HTTP access and tabular pagination."""
import logging
import time
from datetime import datetime

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class Coingecko:
    def __init__(self, base_url=None, auth_key=None, timeout=30):
        self.base_url = (base_url or "https://api.coingecko.com/api/v3").rstrip("/")
        self.auth_key = auth_key
        self.headers = {"x-cg-pro-api-key": auth_key} if auth_key else {}
        self.timeout = timeout

    def get_api_data(self, detail_url="", params=None, max_retries=30, sleep=60):
        if max_retries < 1 or sleep < 0:
            raise ValueError("max_retries must be positive and sleep nonnegative")
        url = f"{self.base_url}/{detail_url.lstrip('/')}"
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=dict(params or {}),
                                        headers=self.headers, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout):
                if attempt == max_retries - 1:
                    raise
            else:
                if response.status_code != 429 and response.status_code < 500:
                    response.raise_for_status()
                    return response
                if attempt == max_retries - 1:
                    response.raise_for_status()
            logger.warning("Request failed for %s; retry %s/%s", detail_url,
                           attempt + 1, max_retries)
            time.sleep(sleep)

    def get_data(self, detail_url, params=None, _ts=None, rename=None,
                 sleep=60, max_retries=30):
        payload = self.get_api_data(detail_url, params, sleep=sleep,
                                    max_retries=max_retries).json()
        data = pd.DataFrame(payload)
        if not data.empty:
            data["_ts"] = _ts if _ts is not None else datetime.now().astimezone()
        return data.rename(columns=rename) if rename else data

    def get_page_data(self, detail_url="coins/markets", start_pages=1,
                      end_pages=10, params=None, rename=None, sleep=500,
                      max_retries=10):
        if not 1 <= start_pages <= end_pages:
            raise ValueError("Require 1 <= start_pages <= end_pages")
        frames = []
        timestamp = datetime.now().astimezone()
        for page in range(start_pages, end_pages + 1):
            page_params = {**(params or {}), "page": page}
            logger.info("Get data (%s/%s)", page, end_pages)
            frame = self.get_data(detail_url, page_params, _ts=timestamp,
                                  rename=rename, sleep=sleep, max_retries=max_retries)
            if frame.empty:
                break
            frames.append(frame)
            if len(frame) < int(page_params.get("per_page", 0)):
                break
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
