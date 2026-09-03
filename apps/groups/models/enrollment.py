from django.db import models
from django.db.models import Q, F
from django.core.validators import MaxValueValidator, MinValueValidator
from apps.users.models import Student
from .group import Group



class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT)
    group = models.ForeignKey(Group, on_delete=models.PROTECT)

    start_date = models.DateField()
    end_date = models.DateField(null=True)

    discount_percent = models.PositiveSmallIntegerField(
            default=0,
            validators=[
                MinValueValidator(0),
                MaxValueValidator(100),
            ]
        )


    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        FINISHED = "finished", "Finished"
        DROPPED = "dropped", "Dropped"

    status = models.CharField(
        max_length=250,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "group", "start_date"],
                name="unique_student_group_start_date"
            ),
            models.CheckConstraint(
                condition=Q(end_date__isnull=True) | Q(end_date__gte=F("start_date")),
                name="end_date_gte_start_date",
            ),
        ]
        indexes = [
            models.Index(
                fields=['student', 'group'],
                name='enrollment_student_group_idx',
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.group}"

