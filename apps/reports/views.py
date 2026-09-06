from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.groups.models import Group
from apps.reports.services import (
    attendance_summary,
    debtors_queryset,
    monthly_report,
    student_debt,
)
from apps.users.models import Student
from apps.users.permissions import IsAdmin, IsAdminOrTeacher


class DebtorsReportView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        group_id = request.query_params.get("group")
        min_debt = request.query_params.get("min_debt", 1)
        try:
            min_debt = int(min_debt or 1)
        except ValueError:
            min_debt = 1

        qs = debtors_queryset(min_debt=min_debt)
        if group_id:
            qs = qs.filter(group_id=group_id)

        data = []
        for e in qs:
            data.append(
                {
                    "enrollment_id": e.id,
                    "student_id": e.student_id,
                    "full_name": e.student.user.full_name,
                    "phone": e.student.user.phone,
                    "group_id": e.group_id,
                    "group_name": e.group.name,
                    "monthly_price": str(e.monthly),
                    "months": e.months,
                    "expected": str(e.expected),
                    "paid": str(e.paid),
                    "debt": str(e.debt),
                }
            )

        total_debt = sum(
            e.debt for e in qs
        )
        return Response(
            {
                "count": len(data),
                "total_debt": str(total_debt),
                "debtors": data,
            }
        )


class MonthlyReportView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        try:
            year = int(request.query_params.get("year", timezone.localdate().year))
        except ValueError:
            year = timezone.localdate().year
        try:
            month = int(request.query_params.get("month", timezone.localdate().month))
        except ValueError:
            month = timezone.localdate().month

        groups, totals = monthly_report(year, month)

        data = []
        for g in groups:
            collection_percent = (
                round(g.collected / g.expected * 100, 1) if g.expected else 0
            )
            data.append(
                {
                    "group_id": g.id,
                    "group_name": g.name,
                    "teacher": g.teacher.full_name,
                    "active_students": g.active_students,
                    "expected": str(g.expected),
                    "collected": str(g.collected),
                    "debt": str(g.debt),
                    "collection_percent": collection_percent,
                }
            )

        return Response(
            {
                "year": year,
                "month": month,
                "groups": data,
                "totals": {
                    "expected": str(totals["expected"]),
                    "collected": str(totals["collected"]),
                    "debt": str(totals["debt"]),
                },
            }
        )


class StudentDebtReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [IsAuthenticated()]

    def get(self, request, student_id):
        student = get_object_or_404(
            Student.objects.select_related("user"), pk=student_id
        )
        if request.user.role == "student" and student.user_id != request.user.id:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Bu ma'lumot faqat o'z egasi uchun.")

        enrollments = student_debt(student)

        data = []
        total_debt = 0
        for e in enrollments:
            data.append(
                {
                    "enrollment_id": e.id,
                    "group_id": e.group_id,
                    "group_name": e.group.name,
                    "monthly_price": str(e.monthly),
                    "discount_percent": e.discount_percent,
                    "months": e.months,
                    "expected": str(e.expected),
                    "paid": str(e.paid),
                    "debt": str(e.debt),
                }
            )
            total_debt += e.debt or 0

        return Response(
            {
                "student_id": student.id,
                "full_name": student.user.full_name,
                "enrollments": data,
                "total_debt": str(total_debt),
            }
        )


class AttendanceSummaryReportView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrTeacher]

    def get(self, request):
        group_id = request.query_params.get("group")
        student_id = request.query_params.get("student")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if (
            request.user.role == "teacher"
            and group_id
            and not Group.objects.filter(id=group_id, teacher=request.user).exists()
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Bu guruh sizga biriktirilmagan.")

        data = attendance_summary(
            group_id=group_id,
            student_id=student_id,
            date_from=date_from,
            date_to=date_to,
        )

        if request.user.role == "teacher":
            my_group_ids = set(
                Group.objects.filter(teacher=request.user).values_list("id", flat=True)
            )
            data = [row for row in data if row["group_id"] in my_group_ids]

        return Response(data)