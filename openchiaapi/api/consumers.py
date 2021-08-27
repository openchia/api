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
            except Exception:
                pass

    def run(self):
        global LOG_THREAD
        queue = []
        self.watch_manager = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(self.watch_manager)

        self.fp = open(LOG_PATH, encoding='utf-8', errors='ignore')
        seek = os.stat(LOG_PATH).st_size - 2000
        if seek > 0:
            self.fp.seek(seek)
            self._last = self.fp.read().split('\n')[-LOG_LINES:]
            self.send(json.dumps({"data": '\n'.join(self._last)}))

        self.watch_manager.add_watch(
            [LOG_PATH, os.path.dirname(LOG_PATH)],
            pyinotify.IN_CREATE | pyinotify.IN_MODIFY,
            functools.partial(self._follow_callback, queue),
        )

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

    def _follow_callback(self, queue, event):
        if event.mask == pyinotify.IN_MODIFY:
            data = self.fp.read()
            if data:
                queue.append(data)
        elif event.mask == pyinotify.IN_CREATE and event.pathname == LOG_PATH:
            self.fp.close()
            self.fp = open(LOG_PATH, encoding='utf-8', errors='ignore')


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
