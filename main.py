"""Run one configured collection job."""
import argparse
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from src.api import Coingecko
from src import processing
from src.utils import load_config, create_db_engine, Postgres_connect

ROOT = Path(__file__).resolve().parent
HANDLERS = {
    "coins_markets": processing.upload_coins_markets,
    "coins_list": processing.upload_coin_list,
    "asset_platforms": processing.upload_asset_platforms,
    "categories_list": processing.upload_categories_list,
    "categories": processing.upload_categories,
    "exchanges_list": processing.upload_exchanges_list,
    "exchanges": processing.upload_exchanges,
    "derivatives": processing.upload_derivatives,
    "derivatives_exchanges": processing.upload_derivatives_exchanges,
    "derivatives_exchanges_list": processing.upload_derivatives_exchanges_list,
    "trending": processing.upload_trending,
    "global": processing.upload_global,
    "nfts_list": processing.upload_nfts_list,
    "companies_treasury": processing.upload_companies_treasury,
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=HANDLERS)
    args = parser.parse_args(argv)
    conf = load_config(*(ROOT / "conf" / name for name in
                         ("webhook.yml", "logging.yml", "data.yml")))
    log = conf["logging"]
    log_path = Path(log["file_name"])
    if not log_path.is_absolute():
        log_path = ROOT / log_path
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=log["level"].removeprefix("logging."), format=log["format"],
        handlers=[TimedRotatingFileHandler(log_path, when=log["when"],
                  interval=log["interval"], backupCount=log["backupCount"]),
                  logging.StreamHandler()],
    )
    api = Coingecko(auth_key=os.environ.get("COINGECKO_API_KEY") or os.environ.get("api_key"),
                    base_url=os.environ.get("COINGECKO_BASE_URL"))
    engine = create_db_engine(os.environ)
    try:
        db = Postgres_connect(engine)
        job_conf = conf["data"][args.mode]
        if args.mode == "coins_markets":
            data = processing.preprocessing_coins_markets(api.get_page_data(
                detail_url=job_conf["url"], params=job_conf["params"],
                end_pages=job_conf["max_pages"]))
            processing.upload_coins_markets(db, api, job_conf, data=data)
            processing.webhook_coins_markets(api, job_conf, conf["webhook"], data=data)
        else:
            HANDLERS[args.mode](db, api, job_conf)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
