from rest_framework import serializers

from apps.groups.models import Group
from apps.users.models.user import User


class GroupSerializer(serializers.ModelSerializer):
    active_students_count = serializers.IntegerField(read_only=True)
    teacher_full_name = serializers.CharField(source="teacher.full_name", read_only=True)

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "subject",
            "teacher",
            "teacher_full_name",
            "monthly_price",
            "start_date",
            "end_date",
            "lesson_days",
            "lesson_time",
            "room",
            "is_active",
            "active_students_count",
        ]

    def validate_teacher(self, value):
        if value.role != User.Role.TEACHER:
            raise serializers.ValidationError(
                "Guruh o'qituvchisi roli 'teacher' bo'lishi kerak."
            )
        return value

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "Yopilish sanasi boshlanish sanasidan oldin bo'lishi mumkin emas."}
            )
        return attrs
