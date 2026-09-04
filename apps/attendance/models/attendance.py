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

    """ Kim belgilagani miso qaysi ustoz """
    marked_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    " oxirgi marta o'zgartirilgan vaqti "
    marked_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('lesson', 'student')

        indexes = [
            models.Index(
                fields=('student', 'status'),
            ),
        ]

    def clean(self):
        super().save()
        if hasattr(self, 'lesson') and hasattr(self, 'student'):
            group = self.lesson.group


            is_active_member = group.members.filter(
                student = self.student,
                is_active = True
            ).exists()

            if not is_active_member:
                raise ValidationError(
                    f"Faqat faol o'quvchilar ro'yxatidagi o'quvchi yozila olishi mumkin."
                    f"'{self.student}' o'quvchi bu guruhimizda faol emas!!!"
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return  super().save(*args, **kwargs)





