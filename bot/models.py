from django.contrib.auth.models import AbstractUser
from django.db import models

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
