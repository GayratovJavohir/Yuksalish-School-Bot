from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
from bot.models import ReadingSubmission, Book, CustomBook
import logging

logger = logging.getLogger(__name__)

from django.db import transaction

class ReadingService:
    @staticmethod
    @sync_to_async
    def create_reading_submission(student, month, voice_message_id, book=None, custom_book=None):
        try:
            with transaction.atomic():
                submission_data = {
                    "student": student,
                    "month": month,
                    "voice_message_id": voice_message_id,
                }
                if book:
                    submission_data["book"] = book
                if custom_book:
                    submission_data["custom_book"] = custom_book

                submission = ReadingSubmission.objects.create(**submission_data)
                return submission
        except Exception as e:
            logger.error(f"Error creating reading submission: {str(e)}", exc_info=True)
            raise

    @staticmethod
    @sync_to_async
    def save_submission_voice_file(submission, filename, file_content):
        submission.voice_file.save(filename, ContentFile(file_content))
        submission.save()
        return submission

    @staticmethod
    @sync_to_async
    def update_submission_page_count(submission_id, page_count):
        submission = ReadingSubmission.objects.get(id=submission_id)
        submission.page_count = page_count
        submission.save()
        return submission

    @staticmethod
    @sync_to_async
    def delete_submission(submission):
        submission.delete()