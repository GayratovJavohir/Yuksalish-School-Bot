# schoolbot/celery.py
from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import timedelta
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolbot.settings')

app = Celery('schoolbot')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Beat Schedule - now runs every 5 minutes
app.conf.beat_schedule = {
    '5min-reminder': {
        'task': 'bot.tasks.send_daily_reminders',
        'schedule': timedelta(minutes=5),  # Every 5 minutes
    },
}