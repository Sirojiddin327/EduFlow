from rest_framework import serializers
from apps.lessons.models import Lesson


class LessonSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    created_by_full_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "group",
            "group_name",
            "date",
            "topic",
            "is_held",
            "cancel_reason",
            "created_by",
            "created_by_full_name",
            "created_at",
        ]
        read_only_fields = ["created_at", "created_by"]

    def validate_date(self, value):
        from django.utils import timezone
        if value > timezone.localdate():
            raise serializers.ValidationError("Kelajakdagi sana bo'lishi mumkin emas.")
        return value