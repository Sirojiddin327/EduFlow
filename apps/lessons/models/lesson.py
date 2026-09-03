from django.db import models
from apps.groups.models.group import Group
from apps.users.models.user import User

class Lesson(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date = models.DateField()
    topic = models.CharField(max_length=200)
    is_held = models.BooleanField(default=True)
    cancel_reason = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['group', 'date'],
                name='unique_group_lesson_date'
            )
        ]

        indexes = [
            models.Index(
                fields=["group", "date"],
                name="lesson_group_date_idx"
            )
        ]

    def __str__(self):
        return f"{self.group} - {self.date} - {self.topic}"
    