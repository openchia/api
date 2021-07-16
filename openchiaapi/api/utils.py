from asgiref.sync import async_to_sync
import cachetools
import requests

from chia.cmds.farm_funcs import get_average_block_time
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.ints import uint16
from django.conf import settings


@cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=3600))
def get_pool_info():
    url = f'{settings.POOL_URL}/pool_info'
    with requests.get(url) as r:
        assert r.status_code == 200
        return r.json()


async def get_node_info():
    config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
    node_rpc_client = await FullNodeRpcClient.create(
        config["self_hostname"], uint16(8555), DEFAULT_ROOT_PATH, config
    )
    blockchain_state = await node_rpc_client.get_blockchain_state()
    node_rpc_client.close()
    await node_rpc_client.await_closed()
    return blockchain_state


async def estimated_time_to_win(pool_size, blockchain_space=None):
    if blockchain_space is None:
        blockchain_space = (await get_node_info())['space']
    proportion = pool_size / blockchain_space if blockchain_space else -1
    minutes = int((await get_average_block_time(None) / 60) / proportion) if proportion else -1
    return minutes


get_node_info_sync = cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=600))(async_to_sync(get_node_info))
estimated_time_to_win_sync = cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=600))(async_to_sync(estimated_time_to_win))
