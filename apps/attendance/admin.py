from django.contrib import admin

from apps.attendance.models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        "lesson",
        "student",
        "status",
        "comment",
        "marked_by",
        "marked_at",
    ]
    list_filter = ["status"]
    search_fields = [
        "student__user__full_name",
        "lesson__group__name",
    ]
    autocomplete_fields = ["lesson", "student", "marked_by"]
    readonly_fields = ["marked_at"]
