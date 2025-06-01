from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.db.models.signals import post_migrate
from django.dispatch import receiver

def create_daily_notification_task():
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=1,
        period=IntervalSchedule.DAYS,
    )

    task, created = PeriodicTask.objects.get_or_create(
        name='daily-notification-task',
        defaults={
            'interval': schedule,
            'task': 'bot.tasks.send_daily_reminders',
        }
    )

@receiver(post_migrate)
def create_periodic_tasks(sender, **kwargs):
    create_daily_notification_task()
