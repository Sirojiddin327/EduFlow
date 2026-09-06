from datetime import date
from decimal import Decimal

from django.utils import timezone
from django.test import TestCase

from apps.attendance.models import Attendance
from apps.groups.models import Enrollment, Group
from apps.lessons.models import Lesson
from apps.payments.models import Payment
from apps.reports.services import (
    attendance_summary,
    debtors_queryset,
    monthly_report,
    student_debt,
)
from apps.users.models import User, Student


class BaseReportTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="pass", phone="+998901000001",
            full_name="Admin", role=User.Role.ADMIN,
        )
        self.teacher = User.objects.create_user(
            username="teacher", password="pass", phone="+998901000002",
            full_name="O'qituvchi", role=User.Role.TEACHER,
        )
        self.group = Group.objects.create(
            name="Python-12",
            subject="Python",
            teacher=self.teacher,
            monthly_price="500000.00",
            start_date=date(2026, 1, 15),
            lesson_days="du,chor,jum",
            lesson_time="14:00",
            room="101",
        )

    def make_student(self, full_name, phone):
        user = User.objects.create_user(
            username=phone, password="pass", phone=phone,
            full_name=full_name, role=User.Role.STUDENT,
        )
        return Student.objects.create(
            user=user, birth_date=date(2010, 1, 1), parent_name="Ota-ona",
        )


class DebtorTests(BaseReportTest):
    def test_no_payment_student_debt_is_full_amount(self):
        student = self.make_student("Aliyev Ali", "+998901111111")
        Enrollment.objects.create(
            student=student, group=self.group,
            start_date=date(2026, 1, 10), discount_percent=0,
        )
        debts = debtors_queryset()
        self.assertEqual(debts.count(), 1)
        en = debts.first()
        self.assertEqual(en.student, student)
        self.assertEqual(en.paid, Decimal("0"))
        expected = Decimal(9 * 500000)
        self.assertEqual(en.debt, expected)

    def test_fully_paid_student_has_no_debt(self):
        student = self.make_student("Valiyev Vali", "+998902222222")
        en = Enrollment.objects.create(
            student=student, group=self.group,
            start_date=date(2026, 1, 10), discount_percent=0,
        )
        for i in range(9):
            Payment.objects.create(
                enrollment=en, amount="500000.00",
                period=date(2026, 1 + i, 1), paid_at=timezone.localdate(),
                method="cash", created_by=self.admin,
            )
        self.assertEqual(debtors_queryset().count(), 0)

    def test_paid_partly_student_debt_is_remaining(self):
        student = self.make_student("Bekov Bek", "+998909999999")
        en = Enrollment.objects.create(
            student=student, group=self.group,
            start_date=date(2026, 1, 10), discount_percent=0,
        )
        Payment.objects.create(
            enrollment=en, amount="1000000.00",
            period=date(2026, 1, 1), paid_at=timezone.localdate(),
            method="card", created_by=self.admin,
        )
        debts = debtors_queryset()
        en = debts.first()
        self.assertEqual(en.paid, Decimal("1000000"))
        self.assertEqual(en.debt, Decimal(9 * 500000 - 1000000))

    def test_discounted_student_debt_reduced(self):
        student = self.make_student("Karimov Karim", "+998903333333")
        Enrollment.objects.create(
            student=student, group=self.group,
            start_date=date(2026, 1, 10), discount_percent=20,
        )
        grouped = {e.student_id: e for e in student_debt(student)}
        en = grouped[student.id]
        self.assertEqual(en.monthly, Decimal("400000"))
        # 9 oy × 400000 = 3600000, 20% chegirma bilan
        self.assertEqual(en.expected, Decimal(9 * 400000))

    def test_left_student_months_stops_at_exit_month(self):
        student = self.make_student("Saidov Said", "+998904444444")
        Enrollment.objects.create(
            student=student, group=self.group,
            start_date=date(2025, 9, 10),
            end_date=date(2025, 11, 25),
            discount_percent=0,
        )
        grouped = {e.student_id: e for e in student_debt(student)}
        en = grouped[student.id]
        self.assertEqual(en.months, 3)
        self.assertEqual(en.debt, Decimal(3 * 500000))

    def test_multiple_groups_debt_separate(self):
        g2 = Group.objects.create(
            name="English-3", subject="Ingliz tili",
            teacher=self.teacher, monthly_price="300000.00",
            start_date=date(2026, 2, 1), lesson_days="se",
            lesson_time="16:00", room="102",
        )
        student = self.make_student("Rashidov Rashid", "+998905555555")
        e1 = Enrollment.objects.create(
            student=student, group=self.group,
            start_date=date(2026, 1, 10), discount_percent=0,
        )
        Enrollment.objects.create(
            student=student, group=g2,
            start_date=date(2026, 2, 5), discount_percent=0,
        )
        Payment.objects.create(
            enrollment=e1, amount="500000.00",
            period=date(2026, 1, 1), paid_at=timezone.localdate(),
            method="cash", created_by=self.admin,
        )
        # Oylar: Jan-Sep = 9, Feb-Sep = 8
        grouped = {e.group_id: e for e in student_debt(student)}
        self.assertEqual(grouped[self.group.id].debt, Decimal(9 * 500000 - 500000))
        self.assertEqual(grouped[g2.id].debt, Decimal(8 * 300000))


class MonthlyReportTests(BaseReportTest):
    def test_monthly_report_counts_active_students(self):
        s1 = self.make_student("Aliyev Ali", "+998901111111")
        s2 = self.make_student("Valiyev Vali", "+998902222222")
        e1 = Enrollment.objects.create(
            student=s1, group=self.group,
            start_date=date(2026, 1, 10), discount_percent=0,
        )
        Enrollment.objects.create(
            student=s2, group=self.group,
            start_date=date(2025, 12, 5),
            end_date=date(2026, 1, 31), discount_percent=0,
        )
        Payment.objects.create(
            enrollment=e1, amount="500000.00",
            period=date(2026, 1, 1), paid_at=date(2026, 1, 10),
            method="cash", created_by=self.admin,
        )
        groups, totals = monthly_report(2026, 1)
        data = {g.id: g for g in groups}
        row = data[self.group.id]
        self.assertEqual(row.active_students, 2)
        self.assertEqual(row.expected, Decimal("1000000"))
        self.assertEqual(row.collected, Decimal("500000"))
        self.assertEqual(row.debt, Decimal("-500000"))
        self.assertEqual(totals["expected"], Decimal("1000000"))
        self.assertEqual(totals["collected"], Decimal("500000"))

    def test_monthly_report_empty_group(self):
        groups, totals = monthly_report(2026, 5)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].active_students, 0)
        self.assertEqual(groups[0].expected, Decimal("0"))


class AttendanceSummaryTests(BaseReportTest):
    def test_attendance_summary(self):
        s1 = self.make_student("Aliyev Ali", "+998901111111")
        s2 = self.make_student("Valiyev Vali", "+998902222222")
        Enrollment.objects.create(
            student=s1, group=self.group,
            start_date=date(2026, 1, 10), discount_percent=0,
        )
        Enrollment.objects.create(
            student=s2, group=self.group,
            start_date=date(2026, 1, 10), discount_percent=0,
        )
        l1 = Lesson.objects.create(
            group=self.group, date=date(2026, 3, 2),
            topic="Dars 1", created_by=self.teacher,
        )
        l2 = Lesson.objects.create(
            group=self.group, date=date(2026, 3, 4),
            topic="Dars 2", created_by=self.teacher,
        )
        Attendance.objects.create(
            lesson=l1, student=s1, status="present", marked_by=self.teacher,
        )
        Attendance.objects.create(
            lesson=l2, student=s1, status="late", marked_by=self.teacher,
        )
        Attendance.objects.create(
            lesson=l1, student=s2, status="absent", marked_by=self.teacher,
        )

        data = attendance_summary(group_id=self.group.id)
        by_student = {row["student_id"]: row for row in data}
        self.assertEqual(by_student[s1.id]["held_lessons"], 2)
        self.assertEqual(by_student[s1.id]["present"], 1)
        self.assertEqual(by_student[s1.id]["late"], 1)
        self.assertEqual(by_student[s1.id]["percent"], 100.0)
        self.assertEqual(by_student[s2.id]["percent"], 0.0)