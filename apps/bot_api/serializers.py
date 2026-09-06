from rest_framework import serializers

from apps.users.models import User


class BotLinkSerializer(serializers.Serializer):
    phone = serializers.CharField()
    telegram_id = serializers.IntegerField()
    code = serializers.CharField(required=False, allow_blank=True)

    def validate_phone(self, value):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits.startswith("8"):
            digits = "9" + digits[1:]
        normalized = "+" + digits
        if not normalized.startswith("+998") or len(normalized) != 13:
            raise serializers.ValidationError(
                "Telefon raqami +998XXXXXXXXX formatida bo'lishi kerak."
            )
        return normalized


class BotWhoamiSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "role", "phone", "telegram_id"]