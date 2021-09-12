import cachetools
import logging
import requests

from django.conf import settings

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
