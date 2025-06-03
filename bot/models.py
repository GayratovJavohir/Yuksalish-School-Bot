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
    branch = models.ForeignKey("Branch", on_delete=models.SET_NULL, null=True, blank=True)
    student_class = models.ForeignKey("StudentClass", on_delete=models.SET_NULL, null=True, blank=True)
    telegram_id = models.BigIntegerField(blank=True, null=True, unique=True)

    def __str__(self):
        return self.username

# ========== Book Models ==========

class Branch(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name


class StudentClass(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name


class Book(models.Model):
    MONTH_CHOICES = [(month, month) for month in [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]]
    title = models.CharField(max_length=200)
    month = models.CharField(max_length=20, choices=MONTH_CHOICES)
    file = models.FileField(
        upload_to=book_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])]
    )
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['month', 'title']

    def __str__(self):
        return f"{self.title} ({self.month})"

    def delete(self, *args, **kwargs):
        if self.file and default_storage.exists(self.file.name):
            default_storage.delete(self.file.name)
        super().delete(*args, **kwargs)

class CustomBook(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.month}) by {self.student.username}"

# ========== Student Tasks ==========

class StudentTask(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=100)  # Keep as task_name
    video_file = models.FileField(upload_to=task_video_upload_path)
    submission_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ('add', 'change', 'delete', 'view')
        ordering = ['-submission_date']

    def delete(self, *args, **kwargs):
        if self.video_file and default_storage.exists(self.video_file.name):
            default_storage.delete(self.video_file.name)
        super().delete(*args, **kwargs)

# ========== Reading Submissions ==========

class ReadingSubmission(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    custom_book = models.ForeignKey(CustomBook, on_delete=models.CASCADE, null=True, blank=True)
    voice_file = models.FileField(upload_to=reading_voice_upload_path, null=True, blank=True)
    voice_message_id = models.CharField(max_length=255, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)

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
        book_title = self.book.title if self.book else self.custom_book.title
        return f"{self.student.username} - {book_title} ({self.page_count} pages)"
