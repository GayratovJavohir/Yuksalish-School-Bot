from datetime import datetime
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from bot.models import StudentTask

class TaskService:
    @staticmethod
    @sync_to_async
    def save_video_task_submission(student, task_name, video_bytes, filename):
        submission = StudentTask(
            student=student,
            task_name=task_name,
            submission_date=datetime.now()
        )
        submission.video_file.save(filename, ContentFile(video_bytes))
        submission.save()
        return submission