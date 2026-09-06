from rest_framework import serializers

from apps.groups.models import Enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    student_full_name = serializers.CharField(source="student.user.full_name", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_full_name",
            "group",
            "group_name",
            "start_date",
            "end_date",
            "discount_percent",
            "status",
            "created_at",
        ]
        read_only_fields = ["created_at"]
