from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from apps.users.models import User


class IsAdmin(BasePermission):
    message = "Bu amal faqat administrator uchun."

    def has_permission(self, request: Request, view) -> bool:
        return (
            bool(request.user and request.user.is_authenticated)
            and request.user.role == User.Role.ADMIN
        )


class IsTeacher(BasePermission):
    message = "Bu bo'lim faqat o'qituvchi uchun."

    def has_permission(self, request: Request, view) -> bool:
        return (
            bool(request.user and request.user.is_authenticated)
            and request.user.role == User.Role.TEACHER
        )


class IsAdminOrTeacher(BasePermission):
    message = "Bu bo'lim faqat administrator yoki o'qituvchi uchun."

    def has_permission(self, request: Request, view) -> bool:
        return (
            bool(request.user and request.user.is_authenticated)
            and request.user.role in (User.Role.ADMIN, User.Role.TEACHER)
        )


class IsOwnerStudent(BasePermission):
    """Student/attendance/payment obyektiga faqat o'z egasi (o'quvchi) kira oladi."""

    message = "Ushbu ma'lumot faqat o'z egasiga tegishli."

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if request.user.role == User.Role.ADMIN:
            return True
        if request.user.role == User.Role.TEACHER:
            return IsAdminOrTeacher.has_permission(self, request, view) or True
        student = getattr(obj, "student", None)
        if student is not None:
            return student.user_id == request.user.id
        return obj.user_id == request.user.id

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)