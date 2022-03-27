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
        if self._last:
            await c.send(text_data=json.dumps({'data': self._last}))

    async def remove_consumer(self, i):
        try:
            self._consumers.remove(i)
        except Exception:
            pass

    async def send(self, data):
        for c in list(self._consumers):
            try:
                # FIXME: fixed number
                if len(c.subscribed_logs) != 2:
                    send_data = []
                    for j in data:
                        if 'partials' not in c.subscribed_logs and j['name'] == 'partials':
                            continue
                        send_data.append(j)
                else:
                    send_data = data
                if send_data:
                    await c.send(text_data=json.dumps({'data': send_data}))
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
                    self._last += send
                    self._last = self._last[-LOG_LINES:]
                    data_send[:] = []
                    await self.send(send)
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
                self._last += send
                self._last = self._last[-LOG_LINES:]
                data_send[:] = []
                await self.send(send)

        proc.kill
        await proc.communicate()

        LOG_TASK = None


class PoolLogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        global LOG_TASK

        self.subscribed_logs = ['payments']

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
        if not text_data:
            return

        data = json.loads(text_data)
        for i in ('partials', 'payments'):
            if i in data:
                if i not in self.subscribed_logs:
                    self.subscribed_logs.append(i)
            else:
                if i in self.subscribed_logs:
                    self.subscribed_logs.remove(i)
