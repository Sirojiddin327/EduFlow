from datetime import date
from decimal import Decimal

import django_filters

from apps.payments.models import Payment


class PaymentFilter(django_filters.FilterSet):
    student = django_filters.NumberFilter(field_name="enrollment__student_id")
    group = django_filters.NumberFilter(field_name="enrollment__group_id")
    paid_at_from = django_filters.DateFilter(field_name="paid_at", lookup_expr="gte")
    paid_at_to = django_filters.DateFilter(field_name="paid_at", lookup_expr="lte")

    class Meta:
        model = Payment
        fields = ["enrollment", "student", "group", "period", "method", "paid_at_from", "paid_at_to"]