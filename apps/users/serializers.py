from rest_framework import serializers

from apps.users.models import User, Student


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "role",
            "phone",
            "telegram_id",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "user",
            "full_name",
            "phone",
            "birth_date",
            "parent_name",
            "parent_phone",
            "address",
            "note",
            "created_at",
        ]
        read_only_fields = ["created_at"]
