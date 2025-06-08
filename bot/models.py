from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
import os

# ========== Upload Paths ==========

def book_upload_path(instance, filename):
    return f'books/{instance.month}/{filename}'

def task_video_upload_path(instance, filename):
    return f'tasks/{instance.student.username}/{instance.task_name}/{filename}'

def reading_voice_upload_path(instance, filename):
    """Generate upload path for reading voice files"""
    if instance.book:
        return f'reading_voices/{instance.student.username}/book_{instance.book.id}/{filename}'
    elif instance.custom_book:
        return f'reading_voices/{instance.student.username}/custom_{instance.custom_book.id}/{filename}'
    else:
        return f'reading_voices/{instance.student.username}/unknown/{filename}'

# ========== User Model ==========

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('coordinator', 'Coordinator'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    branch = models.CharField(max_length=100, blank=True, null=True)
    student_class = models.CharField(max_length=100, blank=True, null=True)
    telegram_id = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username

# ========== Book Model ==========
class Book(models.Model):
    title = models.CharField(max_length=255)
    month = models.CharField(max_length=20)
    file = models.FileField(upload_to=book_upload_path, validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])])
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'coordinator'})
    upload_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-upload_date']
        unique_together = ('title', 'month')

    def __str__(self):
        return f"{self.title} ({self.month})"

    @property
    def file_exists(self):
        if self.file:
            return default_storage.exists(self.file.name)
        return False

# ========== Student Task Model ==========
class StudentTask(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    task_name = models.CharField(max_length=255)
    video_file = models.FileField(upload_to=task_video_upload_path, null=True, blank=True, validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi', 'mkv'])])
    submission_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submission_date']
        unique_together = ('student', 'task_name')

    def __str__(self):
        return f"{self.student.username} - {self.task_name}"


# ========== Custom Book Model ==========
class CustomBook(models.Model):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    month = models.CharField(max_length=20)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creation_date']
        unique_together = ('name', 'created_by', 'month')

    def __str__(self):
        return self.name
# ========== Reading Submission Model ==========
class ReadingSubmission(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    custom_book = models.ForeignKey(CustomBook, on_delete=models.CASCADE, null=True, blank=True)
    voice_file = models.FileField(upload_to=reading_voice_upload_path, null=True, blank=True)
    voice_message_id = models.CharField(max_length=255, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    month = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['-submission_date']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'book'],
                name='unique_student_book',
                condition=models.Q(book__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['student', 'custom_book'],
                name='unique_student_custom_book',
                condition=models.Q(custom_book__isnull=False)
            )
        ]

    def clean(self):
        if not self.book and not self.custom_book:
            raise ValidationError("Either book or custom_book must be set.")
        if self.book and self.custom_book:
            raise ValidationError("Only one of book or custom_book can be set.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        book_title = self.book.title if self.book else self.custom_book.name
        return f"{self.student.username} - {book_title} ({self.month})"