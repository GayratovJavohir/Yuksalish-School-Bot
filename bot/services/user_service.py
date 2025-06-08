# services/user_service.py
from asgiref.sync import sync_to_async
from django.contrib.auth import authenticate
from bot.models import CustomUser

class UserService:
    @staticmethod
    @sync_to_async
    def get_user_by_telegram_id(telegram_id):
        return CustomUser.objects.filter(telegram_id=telegram_id).first()

    @staticmethod
    @sync_to_async
    def authenticate_user(username, password):
        return authenticate(username=username, password=password)

    @staticmethod
    @sync_to_async
    def save_user(user):
        user.save()

    @staticmethod
    @sync_to_async
    def set_user_password(user, new_password):
        user.set_password(new_password)
        user.save()

    @staticmethod
    @sync_to_async
    def update_user_field(user, field, value):
        setattr(user, field, value)
        user.save()