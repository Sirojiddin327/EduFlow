from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STUDENT = 'student', 'Student'
        TEACHER = 'teacher', 'Teacher'

    full_name = models.CharField(max_length=200)

    role = models.CharField(    
        max_length=10,
        choices=Role.choices,
        db_index=True
    )

    phone = models.CharField(
        max_length=20,
        unique=True
    )

    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        db_index=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    