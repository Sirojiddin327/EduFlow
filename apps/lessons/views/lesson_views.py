from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.attendance.models import Attendance
from apps.attendance.serializers import (
    AttendanceSerializer,
    AttendanceMarkSerializer,
)
from apps.groups.models import Enrollment
from apps.lessons.filters import LessonFilter
from apps.lessons.models import Lesson
from apps.lessons.serializers.lesson_serializer import LessonSerializer
from apps.users.permissions import IsAdminOrTeacher
from apps.users.models import Student


class LessonViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LessonFilter
    search_fields = ["topic", "group__name"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-date"]
    queryset = Lesson.objects.select_related("group", "created_by").all()

    def get_permissions(self):
        return [IsAdminOrTeacher()]

    def get_queryset(self):
        user = self.request.user
        qs = Lesson.objects.select_related("group__teacher", "created_by")
        if user.role == "teacher":
            qs = qs.filter(group__teacher=user)
        elif user.role == "student":
            student = Student.objects.filter(user=user).first()
            if student:
                return qs.filter(group__enrollment__student=student).distinct()
            return qs.none()
        return qs

    def perform_create(self, serializer):
        group = serializer.validated_data["group"]
        if (
            self.request.user.role == "teacher"
            and group.teacher_id != self.request.user.id
        ):
            raise PermissionDenied("Siz faqat o'z guruhingizga dars yarata olasiz.")
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get", "post"], url_path="attendance")
    def attendance(self, request, pk=None):
        lesson = self.get_object()
        if (
            request.user.role == "teacher"
            and lesson.group.teacher_id != request.user.id
        ):
            raise PermissionDenied("Bu guruh sizga biriktirilmagan.")

        if request.method == "GET":
            qs = (
                Attendance.objects.filter(lesson=lesson)
                .select_related("student__user", "marked_by")
                .order_by("student__user__full_name")
            )
            serializer = AttendanceSerializer(qs, many=True)
            return Response(serializer.data)

        marks = request.data
        if not isinstance(marks, list):
            raise ValidationError("Massiv yuborilishi kerak.")

        mark_serializer = AttendanceMarkSerializer(data=marks, many=True)
        mark_serializer.is_valid(raise_exception=True)

        active_student_ids = Enrollment.objects.filter(
            group=lesson.group,
            status=Enrollment.Status.ACTIVE,
            student__user__is_active=True,
        ).values_list("student_id", flat=True)
        active_student_ids = set(active_student_ids)

        student_ids = {m["student"] for m in mark_serializer.validated_data}
        invalid = student_ids - active_student_ids
        if invalid:
            raise ValidationError(
                "Faqat guruhning faol o'quvchilari uchun davomat yozish mumkin."
            )

        objects = []
        for m in mark_serializer.validated_data:
            objects.append(
                Attendance(
                    lesson=lesson,
                    student_id=m["student"],
                    status=m["status"],
                    comment=m.get("comment", ""),
                    marked_by=request.user,
                )
            )

        Attendance.objects.bulk_create(
            objects,
            update_conflicts=True,
            unique_fields=["lesson", "student"],
            update_fields=["status", "comment", "marked_by"],
        )

        return Response(
            {"detail": f"{len(objects)} ta davomat saqlandi."}
        )