from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.groups.models import Enrollment, Group
from apps.groups.serializers import GroupSerializer, EnrollmentSerializer
from apps.groups.serializers.group_detail_serializer import GroupDetailSerializer
from apps.users.permissions import IsAdmin, IsAdminOrTeacher


class GroupViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "teacher", "subject"]
    search_fields = ["name"]
    ordering_fields = ["name", "start_date", "monthly_price"]
    ordering = ["name"]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Group.objects.select_related("teacher")
            .prefetch_related("enrollment_set__student__user")
            .annotate(
                active_students_count=Count(
                    "enrollment",
                    filter=Q(enrollment__status=Enrollment.Status.ACTIVE),
                    distinct=True,
                )
            )
        )
        if user.role == "teacher":
            qs = qs.filter(teacher=user)
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return GroupDetailSerializer
        return GroupSerializer

    def get_permissions(self):
        if self.action in ("create", "partial_update", "update", "destroy"):
            return [IsAdmin()]
        return [IsAdminOrTeacher()]

    def destroy(self, request, *args, **kwargs):
        from django.utils import timezone

        instance = self.get_object()
        instance.is_active = False
        instance.end_date = timezone.localdate()
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EnrollmentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Enrollment.objects.select_related("student__user", "group__teacher")
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["student", "group", "status"]
    ordering_fields = ["start_date", "end_date", "created_at"]
    ordering = ["-start_date"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "finish"):
            return [IsAdmin()]
        return [IsAdminOrTeacher()]

    def get_queryset(self):
        user = self.request.user
        if user.role == "teacher":
            return super().get_queryset().filter(group__teacher=user)
        return super().get_queryset()

    @action(detail=True, methods=["post"])
    def finish(self, request, pk=None):
        from django.utils import timezone

        enrollment = self.get_object()
        enrollment.end_date = timezone.localdate()
        enrollment.status = Enrollment.Status.FINISHED
        enrollment.save()
        return Response(self.get_serializer(enrollment).data)
