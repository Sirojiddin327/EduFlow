from django.core.exceptions import ValidationError
from django.db import models

from apps.groups.models import Enrollment
from apps.lessons.models import Lesson
from apps.users.models import Student, User


class Attendance(models.Model):
    STATUS_CHOICES = [
        ("present", "Keldi"),
        ("absent", "Kelmadi"),
        ("late", "Kechikdi"),
        ("excused", "Sababli"),
    ]

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="attendances",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    comment = models.CharField(max_length=200, blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.PROTECT)
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("lesson", "student")
        indexes = [
            models.Index(fields=["student", "status"], name="attendance_student_status_idx"),
        ]

    def __str__(self):
        return f"{self.lesson} - {self.student} - {self.status}"

    def clean(self):
        if hasattr(self, "lesson") and hasattr(self, "student"):
            group = self.lesson.group
            is_active_member = Enrollment.objects.filter(
                student=self.student,
                group=group,
                status=Enrollment.Status.ACTIVE,
            ).exists()
            if not is_active_member:
                raise ValidationError(
                    "Faqat faol o'quvchilar ro'yxatidagi o'quvchi yozila olishi mumkin. "
                    f"'{self.student}' o'quvchi bu guruhda faol emas."
                )