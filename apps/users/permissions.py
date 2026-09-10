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
            and request.user.role in (
                User.Role.ADMIN,
                User.Role.TEACHER,
            )
        )

    def has_object_permission(self, request: Request, view, obj) -> bool:
        return self.has_permission(request, view)


class IsOwnerStudent(BasePermission):
    message = "Ushbu ma'lumot faqat o'z egasiga tegishli."

    def has_permission(self, request: Request, view) -> bool:
        return bool(
            request.user and request.user.is_authenticated
        )

    def has_object_permission(self, request: Request, view, obj) -> bool:
        # Admin hamma ma'lumotni ko'ra/ishlata oladi
        if request.user.role == User.Role.ADMIN:
            return True

        # Student faqat o'ziga tegishli ma'lumotni ko'radi
        student = getattr(obj, "student", None)

        if student is not None:
            return student.user_id == request.user.id

        # Agar obyektning o'zi user_id orqali bog'langan bo'lsa
        user_id = getattr(obj, "user_id", None)

        return user_id == request.user.id