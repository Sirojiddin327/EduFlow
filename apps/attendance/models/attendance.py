from django.db import models
from apps.lessons.models import Lesson
from apps.users.models import Student, User
from django.core.exceptions import ValidationError

class Attandance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'xcused'),
    ]

    """ Bu yerda qaysi dars ekanligini belgilanadi """
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE, 
        related_name='attandances'
    )

    """ Bu yerda o'quvchi belgilanadi """
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    """ bunda o'qituvchi izoh yozadi ya'ni nega kelmaganini sababini """
    comment = models.CharField(
        max_length=200,
        blank=True
    )

    marked_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    marked_at = models.DateTimeField(
        auto_now_add=True
    )
