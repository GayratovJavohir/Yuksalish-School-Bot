from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
import os

def book_upload_path(instance, filename):
    return f'books/{instance.month}/{filename}'


def task_video_upload_path(instance, filename):
    return f'tasks/{instance.student.username}/{instance.task_name}/{filename}'

def reading_voice_upload_path(instance, filename):
    return f'reading/{instance.student.username}/{instance.month}/{instance.book.title}/{filename}'

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('coordinator', 'Coordinator'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    branch = models.CharField(max_length=100, blank=True, null=True)
    student_class = models.CharField(max_length=100, blank=True, null=True)
    telegram_id = models.BigIntegerField(blank=True, null=True, unique=True)

    def __str__(self):
        return self.username

class Book(models.Model):
    title = models.CharField(max_length=200)
    MONTH_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December')
    ]
    month = models.CharField(max_length=20, choices=MONTH_CHOICES)
    file = models.FileField(
        upload_to=book_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])]
    )
    uploaded_by = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['month', 'title']
    def __str__(self):
        return f"{self.title} ({self.month})"
    def file_exists(self):
        """Check if the file exists on storage"""
        return self.file and os.path.exists(self.file.path)
    def delete(self, *args, **kwargs):
        """Delete the file when model is deleted"""
        if self.file_exists():
            os.remove(self.file.path)
        super().delete(*args, **kwargs)


class StudentTask(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=100)  # Keep as task_name
    video_file = models.FileField(upload_to=task_video_upload_path)
    submission_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        default_permissions = ('add', 'change', 'delete', 'view')
        ordering = ['-submission_date']

    def delete(self, *args, **kwargs):
        if self.video_file:
            if os.path.isfile(self.video_file.path):
                os.remove(self.video_file.path)
        super().delete(*args, **kwargs)


def reading_voice_upload_path(instance, filename):
    return f'reading_voices/{instance.student.username}/{instance.book.id}/{filename}'

class ReadingSubmission(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    voice_file = models.FileField(upload_to=reading_voice_upload_path, null=True, blank=True)
    voice_message_id = models.CharField(max_length=255, blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submission_date']
        unique_together = ['student', 'book']

    def __str__(self):
        return f"{self.student.username} - {self.book.title}"