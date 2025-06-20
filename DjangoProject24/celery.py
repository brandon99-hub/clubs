# project/celery.py
from __future__ import absolute_import
import os
from django.apps import apps


class Celery:
    def config_from_object(self, param, namespace):
        pass


from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject24.settings')

app = Celery('DjangoProject24')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks defined in installed apps
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

