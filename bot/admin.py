from django.contrib import admin
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from .models import CustomUser, TaskSubmission
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



@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'task_name', 'submitted_at')
    list_filter = ('task_name', 'submitted_at')
    search_fields = ('user__username', 'task_name')
