from datetime import date, timedelta

from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    IntegerField,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.utils import timezone

from apps.attendance.models import Attendance
from apps.groups.models import Enrollment, Group


def _monthly_expression():
    return ExpressionWrapper(
        F("group__monthly_price") * (100 - F("discount_percent")) / 100,
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


def _months_expression(today=None):
    today = today or timezone.localdate()
    return ExpressionWrapper(
        (
            (ExtractYear(Coalesce("end_date", Value(today))) - ExtractYear("start_date"))
            * 12
            + (ExtractMonth(Coalesce("end_date", Value(today))) - ExtractMonth("start_date"))
            + 1
        ),
        output_field=IntegerField(),
    )


def _expected_expression(today=None):
    return ExpressionWrapper(
        _months_expression(today) * _monthly_expression(),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


def debtors_queryset(min_debt=None):
    today = timezone.localdate()
    qs = (
        Enrollment.objects.select_related("student__user", "group__teacher")
        .annotate(
            months=_months_expression(today),
            monthly=_monthly_expression(),
            expected=_expected_expression(today),
        )
        .annotate(
            paid=Coalesce(
                Sum("payments__amount"),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            debt=F("expected") - F("paid"),
        )
    )
    qs = qs.filter(debt__gt=0)
    if min_debt is not None and min_debt > 1:
        qs = qs.filter(debt__gte=min_debt)
    return qs.order_by("-debt")


def student_debt(student):
    today = timezone.localdate()
    return (
        Enrollment.objects.filter(student=student)
        .select_related("group")
        .annotate(
            months=_months_expression(today),
            monthly=_monthly_expression(),
            expected=_expected_expression(today),
        )
        .annotate(
            paid=Coalesce(
                Sum("payments__amount"),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            debt=F("expected") - F("paid"),
        )
        .order_by("group__name")
    )


def monthly_report(year, month):
    oy_boshi = date(year, month, 1)
    oy_oxiri = (date(year, month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    active_q = Q(
        enrollment__start_date__lte=oy_oxiri
    ) & (Q(enrollment__end_date__isnull=True) | Q(enrollment__end_date__gte=oy_boshi))

    groups = (
        Group.objects.filter(is_active=True)
        .select_related("teacher")
        .annotate(
            collected=Coalesce(
                Sum(
                    "enrollment__payments__amount",
                    filter=Q(enrollment__payments__period=oy_boshi),
                ),
                Value(0),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            active_students=Count(
                "enrollment",
                filter=active_q,
                distinct=True,
            ),
            expected=ExpressionWrapper(
                F("monthly_price") * F("active_students"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        .annotate(
            debt=F("collected") - F("expected"),
        )
        .order_by("name")
    )

    totals = {"expected": 0, "collected": 0, "debt": 0}
    for g in groups:
        totals["expected"] += g.expected or 0
        totals["collected"] += g.collected or 0
    totals["debt"] = totals["collected"] - totals["expected"]

    return groups, totals


def attendance_summary(group_id=None, student_id=None, date_from=None, date_to=None):
    held_q = Q(lesson__is_held=True)
    if group_id:
        held_q &= Q(lesson__group_id=group_id)
    if student_id:
        held_q &= Q(student_id=student_id)
    if date_from:
        held_q &= Q(lesson__date__gte=date_from)
    if date_to:
        held_q &= Q(lesson__date__lte=date_to)

    rows = (
        Attendance.objects.filter(held_q)
        .select_related("student__user", "lesson__group")
        .values(
            "student_id",
            "student__user__full_name",
            "lesson__group_id",
            "lesson__group__name",
        )
        .annotate(
            held=Count("lesson", distinct=True),
            present=Count("id", filter=Q(status="present")),
            absent=Count("id", filter=Q(status="absent")),
            late=Count("id", filter=Q(status="late")),
            excused=Count("id", filter=Q(status="excused")),
        )
        .order_by("lesson__group__name", "student__user__full_name")
    )

    result = []
    for row in rows:
        held = row["held"] or 0
        boagan = row["present"] + row["late"]
        percent = round(boagan / held * 100, 1) if held else 0
        result.append(
            {
                "student_id": row["student_id"],
                "full_name": row["student__user__full_name"],
                "group_id": row["lesson__group_id"],
                "group_name": row["lesson__group__name"],
                "held_lessons": held,
                "present": row["present"],
                "absent": row["absent"],
                "late": row["late"],
                "excused": row["excused"],
                "percent": percent,
            }
        )
    return result