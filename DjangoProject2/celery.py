# project/celery.py
from __future__ import absolute_import
import os


class Celery:
    def autodiscover_tasks(self):
        pass

    def config_from_object(self, param, namespace):
        pass


from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

app = Celery('project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover tasks defined in installed apps
app.autodiscover_tasks()


def contrib():
    return None