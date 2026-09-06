from django.urls import path

from apps.reports.views import (
    AttendanceSummaryReportView,
    DebtorsReportView,
    MonthlyReportView,
    StudentDebtReportView,
)

urlpatterns = [
    path("debtors/", DebtorsReportView.as_view(), name="report-debtors"),
    path("monthly/", MonthlyReportView.as_view(), name="report-monthly"),
    path(
        "student-debt/<int:student_id>/",
        StudentDebtReportView.as_view(),
        name="report-student-debt",
    ),
    path(
        "attendance-summary/",
        AttendanceSummaryReportView.as_view(),
        name="report-attendance-summary",
    ),
]