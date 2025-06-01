import os
import django
from celery import Celery
from django.conf import settings

# Initialize Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolbot.settings')
django.setup()

# Now import the scheduler after Django is initialized
from django_celery_beat.schedulers import DatabaseScheduler

app = Celery('schoolbot')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

if __name__ == '__main__':
    beat = app.Beat(
        scheduler=DatabaseScheduler,
        loglevel='info',
        max_interval=300,  # Check for new tasks every 5 minutes
    )
    beat.run()