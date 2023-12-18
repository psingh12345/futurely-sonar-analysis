# pylint: disable=unused-argument
import json, random
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from uuid import uuid4


def schedule_hubspot_update(request):
    dict = {'be_careful': True,}
    task_uuid = str(uuid4)
    print(task_uuid)
    schedule, created = CrontabSchedule.objects.get_or_create(hour = 6 , minute = 59)
    task = PeriodicTask.objects.update_or_create(crontab = schedule, name = f"schedule_hubspot_task{task_uuid}",task = "website.tasks.test_function", args = json.dumps([1,]), kwargs = json.dumps(dict))
    print("Task Created")