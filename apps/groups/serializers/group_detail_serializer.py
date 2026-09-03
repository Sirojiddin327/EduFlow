from rest_framework import serializers

from apps.groups.models import Group, Enrollment
from .enrollment_serializer import EnrollmentSerializer


class GroupDetailSerializer(serializers.ModelSerializer):
    active_students_count = serializers.IntegerField(read_only=True)
    teacher_full_name = serializers.CharField(source="teacher.full_name", read_only=True)
    enrollments = EnrollmentSerializer(many=True, read_only=True)

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
            "enrollments",
        ]
