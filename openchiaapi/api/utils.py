import cachetools
import logging
import requests

from asgiref.sync import async_to_sync
from chia.cmds.farm_funcs import get_average_block_time
from django.conf import settings

logger = logging.getLogger('utils')


@cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=3600))
def get_pool_info():
    url = f'{settings.POOL_URL}/pool_info'
    with requests.get(url) as r:
        assert r.status_code == 200
        return r.json()


async def estimated_time_to_win_async(pool_size, blockchain_space):
    proportion = pool_size / blockchain_space if blockchain_space else -1
    minutes = int((await get_average_block_time(None) / 60) / proportion) if proportion else -1
    return minutes

estimated_time_to_win = async_to_sync(estimated_time_to_win_async)
