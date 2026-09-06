from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from apps.payments.filters import PaymentFilter
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer
from apps.users.models import Student
from apps.users.permissions import IsAdmin


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PaymentFilter
    search_fields = ["enrollment__student__user__full_name", "receipt_no"]
    ordering_fields = ["period", "paid_at", "amount", "created_at"]
    ordering = ["-period", "-created_at"]
    queryset = (
        Payment.objects.select_related(
            "enrollment__student__user", "enrollment__group", "created_by"
        )
        .all()
        .order_by("-period", "-created_at")
    )

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        if user.role == "student":
            student = Student.objects.filter(user=user).first()
            qs = qs.filter(enrollment__student=student) if student else qs.none()
        return qs

    def get_permissions(self):
        if self.action in ("create", "destroy"):
            return [IsAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        try:
            instance.validate_deletable()
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        instance.delete()