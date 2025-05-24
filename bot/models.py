# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('coordinator', 'Coordinator'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    branch = models.CharField(max_length=100, blank=True, null=True)
    student_class = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username
