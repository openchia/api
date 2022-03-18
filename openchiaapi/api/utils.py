import cachetools
import logging
import os
import requests
import yaml

from django.conf import settings

from influxdb_client import InfluxDBClient


_POOL_CONFIG = None
logger = logging.getLogger('utils')


@cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=3600))
def get_pool_info():
    url = f'{settings.POOL_URL}/pool_info'
    with requests.get(url) as r:
        assert r.status_code == 200
        return r.json()


def estimated_time_to_win(pool_size, blockchain_space, avg_block_time):
    proportion = pool_size / blockchain_space if blockchain_space else -1
    minutes = int((avg_block_time / 60) / proportion) if proportion else -1
    return minutes


def get_pool_config():
    global _POOL_CONFIG
    if _POOL_CONFIG is not None:
        return _POOL_CONFIG
    cfg_path = os.environ.get('POOL_CONFIG_PATH') or ''
    if not os.path.exists(cfg_path):
        raise ValueError('POOL_CONFIG_PATH does not exist.')
    with open(cfg_path, 'r') as f:
        cfg = yaml.safe_load(f.read())
    _POOL_CONFIG = cfg
    return _POOL_CONFIG


def get_pool_fees():
    cfg = get_pool_config()
    return cfg['fee']


def get_pool_target_address():
    cfg = get_pool_config()
    return cfg['wallets'][0]['address']


def get_influxdb_client():
    client = InfluxDBClient(
        url=settings.INFLUXDB_URL,
        token=settings.INFLUXDB_TOKEN,
        org=settings.INFLUXDB_ORG,
        ssl=getattr(settings, 'INFLUXDB_SSL', False),
        verify_ssl=getattr(settings, 'INFLUXDB_VERIFY_SSL', False),
    )
    return client


def days_to_every(days):
    if days == 1:
        every = '15m'
    elif days <= 7:
        every = '1h'
    elif days <= 31:
        every = '12h'
    else:
        every = '1d'
    return every
