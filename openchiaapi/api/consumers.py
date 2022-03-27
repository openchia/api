import asyncio
import json
import os
import subprocess
from channels.generic.websocket import AsyncWebsocketConsumer


LOG_DIR = os.environ.get('POOL_LOG_DIR')
LOG_TASK = None
LOG_LINES = 15


class LogTask(object):

    def __init__(self):
        self._consumers = []
        self._last = []

    async def add_consumer(self, c):
        self._consumers.append(c)
        data_send = []
        for i in self._last:
            try:
                data_send.append(json.loads(i))
            except ValueError:
                data_send.append(i)
        await c.send(text_data=json.dumps({'data': data_send}))

    async def remove_consumer(self, i):
        try:
            self._consumers.remove(i)
        except Exception:
            pass

    async def send(self, data):
        for i in list(self._consumers):
            try:
                await i.send(text_data=data)
            except Exception:
                pass

    async def run(self):
        global LOG_TASK

        proc = await asyncio.create_subprocess_exec(
            'tail',
            '-F',
            '-n', str(LOG_LINES),
            os.path.join(LOG_DIR, 'main.log.json'),
            os.path.join(LOG_DIR, 'partial.log.json'),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        data_send = []
        while self._consumers:
            try:
                line = await asyncio.wait_for(proc.stdout.readline(), 1)
            except asyncio.TimeoutError:
                if data_send:
                    send = list(data_send)
                    data_send[:] = []
                    await self.send(json.dumps({"data": send}))
                continue

            if not line:
                break

            if not line.startswith(b'{'):
                continue

            try:
                data_send.append(json.loads(line.decode(errors='ignore')))
            except ValueError:
                pass

            if len(data_send) >= 10:
                send = list(data_send)
                data_send[:] = []
                await self.send(json.dumps({"data": send}))

        proc.kill
        await proc.communicate()

        LOG_TASK = None


class PoolLogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        global LOG_TASK
        await self.accept()

        if not os.path.exists(LOG_DIR):
            return

        if LOG_TASK is None:
            LOG_TASK = LogTask()
            asyncio.create_task(LOG_TASK.run())
        await LOG_TASK.add_consumer(self)

    async def disconnect(self, close_code):
        global LOG_TASK
        if LOG_TASK is not None:
            LOG_TASK.remove_consumer(self)

    async def receive(self, text_data=None, bytes_data=None):
        pass
