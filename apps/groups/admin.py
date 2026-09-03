from django.contrib import admin

from apps.groups.models import Group, Enrollment


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "subject",
        "teacher",
        "monthly_price",
        "start_date",
        "is_active",
    ]
    list_filter = ["is_active", "subject"]
    search_fields = ["name"]
    autocomplete_fields = ["teacher"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "group",
        "start_date",
        "end_date",
        "discount_percent",
        "status",
    ]
    list_filter = ["status"]
    search_fields = ["student__user__full_name", "group__name"]
    autocomplete_fields = ["student", "group"]
