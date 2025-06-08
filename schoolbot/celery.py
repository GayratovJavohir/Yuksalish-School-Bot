from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolbot.settings')

app = Celery('schoolbot')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Schedule for periodic tasks
app.conf.beat_schedule = {
    'send-daily-reminders': {
        'task': 'bot.tasks.send_daily_reminders',
        'schedule': crontab(minute=54, hour=10),  # 9:00 AM daily
    },
}