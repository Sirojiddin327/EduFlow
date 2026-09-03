from django.db import models
from apps.users.models.user import User

class Group(models.Model):
    name = models.CharField(max_length=150)
    subject = models.CharField(max_length=100)
    teacher = models.ForeignKey(User, on_delete=models.PROTECT)
    monthly_price = models.DecimalField(
                        max_digits=10,
                        decimal_places=2
                    )
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    lesson_days = models.CharField(max_length=20)
    lesson_time = models.TimeField()
    room = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    