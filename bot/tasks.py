from celery import shared_task
from datetime import date
from .models import CustomUser, StudentTask
from .utils.telegram import send_message_to_user

@shared_task(bind=True, max_retries=3)
def send_daily_reminders(self):
    today = date.today()
    students = CustomUser.objects.filter(role='student').exclude(telegram_id__isnull=True)

    for student in students:
        submitted = StudentTask.objects.filter(
            student=student,
            submission_date__date=today
        ).exists()

        if not submitted:
            success = send_message_to_user(
                telegram_id=student.telegram_id,
                message="📌 Salom! Bugun hali hech qanday vazifa topshirmadingiz. Iltimos, unutmaslikka harakat qiling!"
            )
            if not success:
                self.retry(countdown=60)  # Retry after 60 seconds if failed