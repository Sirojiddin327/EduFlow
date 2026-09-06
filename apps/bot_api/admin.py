from django.contrib import admin

from apps.bot_api.models import BotLinkCode


@admin.register(BotLinkCode)
class BotLinkCodeAdmin(admin.ModelAdmin):
    list_display = ["user", "code", "attempts", "created_at"]
    search_fields = ["user__full_name", "user__phone"]
    autocomplete_fields = ["user"]
    readonly_fields = ["created_at"]