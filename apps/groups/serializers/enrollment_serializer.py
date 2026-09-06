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

    def validate_discount_percent(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError("Chegirma 0 dan 100 gacha bo'lishi kerak.")
        return value

    def validate(self, attrs):
        if self.instance:
            return attrs

        student = attrs.get("student")
        group = attrs.get("group")

        if student and group:
            active = Enrollment.objects.filter(
                student=student,
                group=group,
                end_date__isnull=True,
            ).exists()
            if active:
                raise serializers.ValidationError(
                    "Bu o'quvchi allaqachon shu guruhda faol a'zo."
                )

            start_date = attrs.get("start_date")
            if start_date and student and group:
                past_active = Enrollment.objects.filter(
                    student=student,
                    group=group,
                    end_date__isnull=False,
                    end_date__gte=start_date,
                ).exists()
                if past_active:
                    raise serializers.ValidationError(
                        "Bu davr uchun allaqachon a'zolik mavjud."
                    )
        return attrs