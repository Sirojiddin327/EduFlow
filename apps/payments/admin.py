from django.contrib import admin

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "enrollment",
        "amount",
        "period",
        "paid_at",
        "method",
        "reciept_no",
        "created_by",
        "created_at",
    ]
    list_filter = ["method", "period"]
    search_fields = [
        "enrollment__student__user__full_name",
        "reciept_no",
    ]
    autocomplete_fields = ["enrollment", "created_by"]
    readonly_fields = ["created_at"]
