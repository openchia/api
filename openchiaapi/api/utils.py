import asyncio
import cachetools
import logging
import multiprocessing
import os
import requests
import signal
import threading
import time

from chia.cmds.farm_funcs import get_average_block_time
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.ints import uint16
from django.conf import settings

logger = logging.getLogger('utils')
BLOCKCHAIN_STATE = None
BLOCKCHAIN_STATE_EVENT = threading.Event()
SHUTTING_DOWN = False


def sighandler(*args, **kwargs):
    global SHUTTING_DOWN
    SHUTTING_DOWN = True
    os.kill(os.getpid(), signal.SIGTERM)

signal.signal(signal.SIGQUIT, sighandler)


@cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=3600))
def get_pool_info():
    url = f'{settings.POOL_URL}/pool_info'
    with requests.get(url) as r:
        assert r.status_code == 200
        return r.json()


def get_node_info():
    return BLOCKCHAIN_STATE or {'space': 0, 'peak': {'height': 0}}


def estimated_time_to_win(pool_size):
    if BLOCKCHAIN_STATE is None:
        return -1
    blockchain_space = BLOCKCHAIN_STATE['space']
    proportion = pool_size / blockchain_space if blockchain_space else -1
    minutes = int((BLOCKCHAIN_STATE['avg_block_time'] / 60) / proportion) if proportion else -1
    return minutes


async def node_loop(child_conn):
    config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
    node_rpc_client = await FullNodeRpcClient.create(
        config["self_hostname"], uint16(8555), DEFAULT_ROOT_PATH, config
    )
    while True:
        blockchain_state = await node_rpc_client.get_blockchain_state()
        blockchain_state['peak'] = {'height': blockchain_state['peak'].height}
        blockchain_state.update({
            'avg_block_time': await get_average_block_time(None),
        })
        child_conn.send(blockchain_state)
        await asyncio.sleep(60)


def blockchain_state(child_conn):
    try:
        asyncio.get_event_loop().run_until_complete(node_loop(child_conn))
    except Exception:
        child_conn.send(EOFError)
        child_conn.close()
        raise


def setup_node_client():
    global BLOCKCHAIN_STATE
    global SHUTTING_DOWN
    while not SHUTTING_DOWN:
        try:
            parent_conn, child_conn = multiprocessing.Pipe(duplex=False)
            process = multiprocessing.Process(
                target=blockchain_state,
                args=(child_conn,),
            )
        except Exception:
            logger.error('Failed starting blockchain state process', exc_info=True)
            time.sleep(5)
            continue

        try:
            process.start()
            while True:
                # FIXME: EOF is not being raised when conn closes
                if parent_conn.poll(2):
                    recv = parent_conn.recv()
                    if recv is EOFError:
                        break
                    BLOCKCHAIN_STATE = recv
                else:
                    if not process.is_alive() or SHUTTING_DOWN:
                        logger.info('Blockchain state process no longer alive')
                        break
            process.terminate()
        except Exception:
            logger.error('Failed getting blockchain state', exc_info=True)
        time.sleep(5)
