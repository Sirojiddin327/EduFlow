from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User, Student
from apps.users.permissions import IsAdmin, IsAdminOrTeacher, IsOwnerStudent
from apps.users.serializers import UserSerializer, StudentSerializer


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["role", "is_active"]
    search_fields = ["full_name", "username", "phone"]
    ordering_fields = ["full_name", "created_at"]
    ordering = ["full_name"]
    queryset = User.objects.all().order_by("full_name")


class StudentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrTeacher]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["user__full_name", "parent_name"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.role == "teacher":
            return (
                Student.objects.filter(enrollment__group__teacher=user)
                .distinct()
                .select_related("user")
            )
        if user.role == "student":
            return Student.objects.filter(user=user).select_related("user")
        return Student.objects.select_related("user").all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [IsAdmin()]
        if self.request.user.is_authenticated and self.request.user.role == "student":
            return [IsAuthenticated(), IsOwnerStudent()]
        return [IsAdminOrTeacher()]


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
