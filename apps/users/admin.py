from django.contrib import admin

from apps.users.models import User, Student


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["full_name", "username", "role", "phone", "is_active"]
    list_filter = ["role", "is_active"]
    search_fields = ["full_name", "username", "phone"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["user", "birth_date", "parent_name", "parent_phone"]
    search_fields = ["user__full_name", "parent_name"]
    autocomplete_fields = ["user"]
