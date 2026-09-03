from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.groups.models.enrollment import Enrollment
from apps.users.models.user import User


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        TRANSFER = "transfer", "Transfer"

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    period = models.DateField()
    paid_at = models.DateField()
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
    )
    receipt_no = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["enrollment", "period"],
                name="payment_enrollment_period_idx",
            ),
            models.Index(
                fields=["period"],
                name="payment_period_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        self.period = self.period.replace(day=1)
        super().save(*args, **kwargs)

    def validate_deletable(self):
        from django.utils import timezone

        if (timezone.localdate() - self.paid_at).days > 30:
            raise ValidationError(
                {"detail": "30 kundan eski to'lovni o'chirish mumkin emas."}
            )

    def __str__(self):
        return f"{self.enrollment} - {self.period} - {self.amount}"