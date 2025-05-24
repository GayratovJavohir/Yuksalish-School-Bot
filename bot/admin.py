# admin.py
from django.contrib import admin
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "branch", "student_class", "is_active")

    def save_model(self, request, obj, form, change):
        if not change and obj.role == "student":
            # Auto generate login va password
            obj.username = obj.username or get_random_string(8)
            password = get_random_string(10)
            obj.password = make_password(password)

            # Bu yerda parolni log qilamiz yoki saqlaymiz (admin ko'rishi uchun)
            # Masalan: log faylga yozish yoki vaqtincha modelda saqlash (yaxshiroq usul: emailing yuborish)
            print(f"Yangi student yaratildi:\nLogin: {obj.username}\nParol: {password}")

        super().save_model(request, obj, form, change)
