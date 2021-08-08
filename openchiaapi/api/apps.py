from django.apps import AppConfig
from api.utils import setup_node_client

import sys
import threading


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        if sys.argv[0:2] == ['manage.py', 'runserver'] or sys.argv[0].endswith('/uvicorn'):
            t = threading.Thread(target=setup_node_client)
            t.start()
