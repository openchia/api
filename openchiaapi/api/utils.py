import cachetools
import logging
import requests

from django.conf import settings

from influxdb_client import InfluxDBClient


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
        every = '1m'
    elif days <= 7:
        every = '1h'
    elif days <= 31:
        every = '12h'
    else:
        every = '1d'
    return every
