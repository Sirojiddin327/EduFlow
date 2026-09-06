from rest_framework import serializers

from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    student_full_name = serializers.CharField(
        source="enrollment.student.user.full_name", read_only=True
    )
    group_name = serializers.CharField(
        source="enrollment.group.name", read_only=True
    )
    created_by_full_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "enrollment",
            "student_full_name",
            "group_name",
            "amount",
            "period",
            "paid_at",
            "method",
            "reciept_no",
            "created_by",
            "created_by_full_name",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("To'lov miqdori 0 dan katta bo'lishi kerak.")
        return value

    def validate(self, attrs):
        enrollment = attrs.get("enrollment")
        period = attrs.get("period", getattr(self.instance, "period", None))

        if enrollment and period:
            existing = Payment.objects.filter(
                enrollment=enrollment,
                period__year=period.year,
                period__month=period.month,
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    {"period": "Bu davr uchun allaqachon to'lov mavjud."}
                )
        return attrs
