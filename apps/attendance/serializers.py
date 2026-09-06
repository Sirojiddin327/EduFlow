from rest_framework import serializers
from apps.attendance.models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_full_name = serializers.CharField(source="student.user.full_name", read_only=True)
    lesson_topic = serializers.CharField(source="lesson.topic", read_only=True)
    lesson_date = serializers.DateField(source="lesson.date", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "lesson",
            "lesson_topic",
            "lesson_date",
            "student",
            "student_full_name",
            "status",
            "comment",
            "marked_by",
            "marked_at",
        ]
        read_only_fields = ["marked_at", "marked_by"]

    def validate_status(self, value):
        valid = ["present", "absent", "late", "excused"]
        if value not in valid:
            raise serializers.ValidationError(
                f"Holat quyidagilardan biri bo'lishi kerak: {', '.join(valid)}"
            )
        return value


class AttendanceMarkSerializer(serializers.Serializer):
    student = serializers.IntegerField()
    status = serializers.ChoiceField(choices=["present", "absent", "late", "excused"])
    comment = serializers.CharField(required=False, allow_blank=True, default="")