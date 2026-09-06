from django.contrib import admin

from apps.lessons.models import Lesson


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        "group",
        "date",
        "topic",
        "is_held",
        "cancel_reason",
        "created_by",
        "created_at",
    ]
    list_filter = ["is_held", "date"]
    search_fields = ["group__name", "topic"]
    autocomplete_fields = ["group", "created_by"]
    readonly_fields = ["created_at"]
