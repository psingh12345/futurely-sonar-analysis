from __future__ import absolute_import, unicode_literals
import os, time
from celery import Celery
from django.conf import settings
from celery.schedules import crontab


# setting the Django settings module.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'thefuturely.settings')
app = Celery('thefuturely')
app.conf.enable_utc = True 
# app.conf.update(result_extended=True)
app.config_from_object(settings, namespace='CELERY')

#Celery beat configuration

# app.conf.beat_schedule = {
#     # 'print-task-by-5min-delay':{
#     #     'task':'website.tasks.test_function',
#     #     'schedule': crontab(hour=13,minute=36)
#     # }
# }

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request :{self.request!r}")
