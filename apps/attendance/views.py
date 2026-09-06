from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.attendance.filters import AttendanceFilter
from apps.attendance.models import Attendance
from apps.attendance.serializers import AttendanceSerializer
from apps.users.permissions import IsAdminOrTeacher


class AttandanceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AttendanceFilter
    search_fields = ["student__user__full_name", "lesson__topic"]
    ordering_fields = ["marked_at", "lesson__date"]
    ordering = ["-marked_at"]
    queryset = (
        Attendance.objects.select_related("student__user", "lesson__group", "marked_by")
        .all()
        .order_by("-marked_at")
    )

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        if user.role == "teacher":
            qs = qs.filter(lesson__group__teacher=user)
        elif user.role == "student":
            qs = qs.filter(student__user=user)
        return qs

    def get_permissions(self):
        if self.request.user.is_authenticated and self.request.user.role == "student":
            return [IsAuthenticated()]
        return [IsAdminOrTeacher()]