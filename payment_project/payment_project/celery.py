import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
# This must happen before the Celery app is created.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_project.settings')

app = Celery('payment_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
# This line will discover tasks in any tasks.py files within your apps.
# For example, it will find tasks in apps/orders/tasks.py
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# To ensure tasks are discovered correctly, especially when apps are in an 'apps' subdirectory,
# it's good practice to help Celery find them if the default autodiscover_tasks() isn't sufficient.
# One way is to provide the app paths explicitly:
# app.autodiscover_tasks(['apps.users', 'apps.orders', 'apps.transactions'])
# However, the lambda version above is generally more robust for discovering from all installed apps.
# Ensure your INSTALLED_APPS in settings.py are correctly named, e.g., 'apps.users.apps.UsersConfig'.

# Django's apps module needs to be imported for the lambda function
from django.apps import apps
