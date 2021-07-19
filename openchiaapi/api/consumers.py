import functools
import json
import os
import pyinotify
import threading
from channels.generic.websocket import WebsocketConsumer


LOG_PATH = os.environ.get('POOL_LOG_PATH') or '/var/log/chia/pool-server.log'

LOG_THREAD = None
LOG_LINES = 15


class LogThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._consumers = []
        self._last = []

    def add_consumer(self, i):
        self._consumers.append(i)
        i.send(text_data=json.dumps({'data': '\n'.join(self._last)}))

    def remove_consumer(self, i):
        global LOG_THREAD
        self._consumers.remove(i)

    def send(self, data):
        for i in list(self._consumers):
            try:
                i.send(text_data=data)
            except Exception as e:
                pass

    def run(self):
        global LOG_THREAD
        queue = []
        watch_manager = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(watch_manager)

        with open(LOG_PATH, encoding='utf-8', errors='ignore') as f:
            seek = os.stat(LOG_PATH).st_size - 2000
            if seek > 0:
                f.seek(seek)
                self._last = f.read().split('\n')[-LOG_LINES:]
                self.send(json.dumps({"data": '\n'.join(self._last)}))

            watch_manager.add_watch(LOG_PATH, pyinotify.IN_MODIFY, functools.partial(self._follow_callback, queue, f))

            while self._consumers:
                notifier.process_events()

                data = "".join(queue)
                if data:
                    self._last += data.split('\n')
                    self._last = self._last[-LOG_LINES:]
                    self.send(json.dumps({"data": data}))
                queue[:] = []

                if notifier.check_events():
                    notifier.read_events()

        notifier.stop()
        LOG_THREAD = None

    def _follow_callback(self, queue, f, event):
        data = f.read()
        if data:
            queue.append(data)


class PoolLogConsumer(WebsocketConsumer):
    def connect(self):
        global LOG_THREAD
        self.accept()
        if LOG_THREAD is None:
            LOG_THREAD = LogThread()
            LOG_THREAD.start()
        LOG_THREAD.add_consumer(self)

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        pass
