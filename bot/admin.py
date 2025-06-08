from django.contrib import admin
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Book, StudentTask, ReadingSubmission, CustomUser
import os

def get_unique_username(length=8, allowed_chars=None):
    if allowed_chars:
        chars = allowed_chars
    else:
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    while True:
        username = get_random_string(length, allowed_chars=chars)
        if not CustomUser.objects.filter(username=username).exists():
            return username


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "first_name", "last_name", "branch", "student_class", "is_active")
    fields = ("username", "role", "branch", "first_name", "last_name", "student_class", "is_active", "password")

    def save_model(self, request, obj, form, change):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        if not change and obj.role == "student":
            obj.username = obj.username or get_unique_username(8)
            student_password = get_random_string(10)
            obj.password = make_password(student_password)

            student_file = os.path.join(base_dir, "student_credentials.txt")
            with open(student_file, "a") as f:
                f.write(f"Login: {obj.username} | Parol: {student_password}\n")

            super().save_model(request, obj, form, change)

            parent_username = f"{obj.username}_p"
            while CustomUser.objects.filter(username=parent_username).exists():
                parent_username = f"{obj.username}_{get_random_string(2)}"

            parent_password = get_random_string(10)

            parent = CustomUser.objects.create(
                role="parent",
                username=parent_username,
                password=make_password(parent_password),
                branch=obj.branch,
                first_name=obj.first_name,
                last_name=obj.last_name,
                student_class=obj.student_class,
                is_active=True,
            )

            parent_file = os.path.join(base_dir, "parent_credentials.txt")
            with open(parent_file, "a") as f:
                f.write(f"Login: {parent_username} | Parol: {parent_password}\n")

            return

        elif not change and obj.role == "parent":
            obj.username = obj.username or get_unique_username(6, allowed_chars='0123456789')
            parent_password = get_random_string(10)
            obj.password = make_password(parent_password)

            parent_file = os.path.join(base_dir, "parent_credentials.txt")
            with open(parent_file, "a") as f:
                f.write(f"Login: {obj.username} | Parol: {parent_password}\n")

        # Coordinator
        elif not change and obj.role == "coordinator":
            obj.username = obj.username or get_unique_username(6, allowed_chars='0123456789')
            coordinator_password = get_random_string(5, allowed_chars='0123456789')
            obj.password = make_password(coordinator_password)

            coordinator_file = os.path.join(base_dir, "coordinator_credentials.txt")

            with open(coordinator_file, "a") as f:
                f.write(f"Login: {obj.username} | Parol: {coordinator_password}\n")

        super().save_model(request, obj, form, change)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not obj:
            fields = tuple(f for f in fields if f != "username")
        return fields


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'month', 'uploaded_by', 'upload_date', 'book_link')
    list_filter = ('month', 'uploaded_by')
    search_fields = ('title', 'month')
    date_hierarchy = 'upload_date'
    raw_id_fields = ('uploaded_by',)

    def book_link(self, obj):
        if obj.file:
            url = reverse('view_book_file', args=[obj.id])
            return mark_safe(f'<a href="{url}" target="_blank">View File</a>')
        return "-"

    book_link.short_description = "File"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StudentTask)
class StudentTaskAdmin(admin.ModelAdmin):
    list_display = ('student', 'task_name', 'submission_date', 'video_link')

    def video_link(self, obj):
        if obj.video_file:
            url = reverse('view_task_video', args=[obj.id])
            return mark_safe(f'<a href="{url}" target="_blank">View Video</a>')
        return "-"

    video_link.short_description = "Video"


@admin.register(ReadingSubmission)
class ReadingSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'get_book_title', 'get_month', 'submission_date', 'voice_preview')
    readonly_fields = ('voice_preview',)
    search_fields = ('student__username', 'book__title', 'custom_book__name') # Corrected custom_book field to 'name'
    list_filter = ('book__month', 'submission_date') # Changed 'month' to 'book__month'

    def get_book_title(self, obj):
        # Corrected for custom_book to use 'name' instead of 'title'
        return obj.book.title if obj.book else obj.custom_book.name if obj.custom_book else "N/A"
    get_book_title.short_description = "Book Title"

    def get_month(self, obj):
        """Retrieves the month from the associated Book object."""
        if obj.book:
            return obj.book.month
        return "N/A" # Or None, or an empty string, depending on desired display
    get_month.short_description = "Month"

    def voice_preview(self, obj):
        if obj.voice_file:
            return mark_safe(f'''
                <audio controls>
                    <source src="{obj.voice_file.url}" type="audio/ogg">
                    Your browser does not support the audio element.
                </audio>
                <a href="{obj.voice_file.url}" download>Download</a>
            ''')
        elif obj.voice_message_id:
            return mark_safe(f'''
                <span>Telegram Voice Message ID: {obj.voice_message_id}</span>
            ''')
        return "No voice file"
    voice_preview.short_description = "Voice Preview"