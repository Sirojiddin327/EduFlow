import random

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.users.models import User


class BotLinkCode(models.Model):
    """Telefon raqam orqali botni akkauntga bog'lash uchun tasdiqlash kodi."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="link_code",
    )
    code = models.CharField(max_length=4)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now=True)

    @classmethod
    def generate_for(cls, user):
        code = f"{random.randint(0, 9999):04d}"
        obj, _ = cls.objects.update_or_create(
            user=user,
            defaults={"code": code, "attempts": 0},
        )
        return obj

    @property
    def is_expired(self):
        # 15 daqiqadan oshgan kod yaroqsiz.
        return (timezone.now() - self.created_at).total_seconds() > 15 * 60