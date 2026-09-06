from django.db import transaction
from rest_framework import serializers

from apps.users.models import User, Student


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "full_name",
            "role",
            "phone",
            "telegram_id",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not validated_data.get("username"):
            validated_data["username"] = validated_data.get("phone")
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name")
    phone = serializers.CharField(source="user.phone")
    username = serializers.CharField(source="user.username", required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    user_readable = UserSerializer(source="user", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "user_readable",
            "full_name",
            "phone",
            "username",
            "password",
            "birth_date",
            "parent_name",
            "parent_phone",
            "address",
            "note",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_phone(self, value):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits.startswith("8"):
            digits = "9" + digits[1:]
        normalized = "+" + digits
        if not normalized.startswith("+998") or len(normalized) != 13:
            raise serializers.ValidationError(
                "Telefon raqami +998XXXXXXXXX formatida bo'lishi kerak."
            )
        if User.objects.filter(phone=normalized).exists():
            raise serializers.ValidationError(
                "Bu telefon raqam allaqachon ro'yxatdan o'tgan."
            )
        return normalized

    def validate_full_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Ism-familiya bo'sh bo'la olmaydi.")
        return value

    def create(self, validated_data):
        with transaction.atomic():
            user_data = validated_data.pop("user", {})
            password = validated_data.pop("password", "") or None
            username = user_data.pop("username", None) or user_data["phone"]
            user = User(
                username=username,
                full_name=user_data["full_name"],
                phone=user_data["phone"],
                role=User.Role.STUDENT,
            )
            if password:
                user.set_password(password)
            else:
                user.set_unusable_password()
            user.save()
            return Student.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            user_data = validated_data.pop("user", {})
            password = validated_data.pop("password", None)

            if password:
                instance.user.set_password(password)
            if user_data.get("full_name"):
                instance.user.full_name = user_data["full_name"]
            if user_data.get("username"):
                instance.user.username = user_data["username"]
            if user_data.get("phone"):
                instance.user.phone = user_data["phone"]
            instance.user.save()

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
        return instance