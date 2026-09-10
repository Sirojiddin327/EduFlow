import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from apps.users.models import User, Student
from apps.groups.models import Group, Enrollment
from apps.lessons.models import Lesson
from apps.attendance.models import Attendance
from apps.payments.models import Payment


fake = Faker("uz_UZ")

SUBJECTS = [
    "Python dasturlash", "Web dasturlash", "Matematika",
    "Ingliz tili", "Rus tili", "Fizika", "Biologiya",
    "Tarix", "Geografiya", "Informatika",
]

LESSON_DAYS_OPTIONS = [
    "Dushanba, Chorshanba, Juma",
    "Seshanba, Payshanba, Shanba",
    "Dushanba, Seshanba, Chorshanba",
    "Payshanba, Juma, Shanba",
    "Dushanba, Chorshanba",
    "Seshanba, Payshanba",
]

ROOMS = [f"Xona-{i}" for i in range(1, 21)]

ATTENDANCE_WEIGHTS = [0.70, 0.15, 0.10, 0.05]  # present, absent, late, excused
ATTENDANCE_STATUSES = ["present", "absent", "late", "excused"]


def gen_phone():
    return f"+998{random.randint(90, 99)}{random.randint(1000000, 9999999)}"


class Command(BaseCommand):
    help = "Bazani test ma'lumotlari bilan to'ldirish (Faker)"

    def add_arguments(self, parser):
        parser.add_argument("--teachers", type=int, default=5, help="O'qituvchilar soni")
        parser.add_argument("--students", type=int, default=40, help="O'quvchilar soni")
        parser.add_argument("--groups", type=int, default=8, help="Guruhlar soni")
        parser.add_argument("--clear", action="store_true", help="Mavjud ma'lumotlarni tozalash")

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Mavjud ma'lumotlar tozalanmoqda...")
            Payment.objects.all().delete()
            Attendance.objects.all().delete()
            Lesson.objects.all().delete()
            Enrollment.objects.all().delete()
            Group.objects.all().delete()
            Student.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING("Barcha ma'lumotlar tozalandi."))

        teachers = self._create_teachers(options["teachers"])
        students = self._create_students(options["students"])
        groups = self._create_groups(teachers, options["groups"])
        enrollments = self._create_enrollments(students, groups)
        lessons = self._create_lessons(groups)
        self._create_attendance(lessons, enrollments)
        self._create_payments(enrollments)

        self.stdout.write(self.style.SUCCESS(
            "\n=== Seed muvaffaqiyatli yakunlandi! ===\n"
            f"  O'qituvchilar: {len(teachers)}\n"
            f"  O'quvchilar:   {len(students)}\n"
            f"  Guruhlar:      {len(groups)}\n"
            f"  Yozilmalar:    {Enrollment.objects.count()}\n"
            f"  Darslar:       {Lesson.objects.count()}\n"
            f"  Davomat:       {Attendance.objects.count()}\n"
            f"  To'lovlar:     {Payment.objects.count()}"
        ))

    def _create_teachers(self, count):
        teachers = []
        used_phones = set()
        for i in range(count):
            phone = gen_phone()
            while phone in used_phones:
                phone = gen_phone()
            used_phones.add(phone)

            user = User.objects.create_user(
                username=phone,
                full_name=fake.name(),
                role=User.Role.TEACHER,
                phone=phone,
                email=fake.email(),
                password="teacher123",
            )
            teachers.append(user)
            self.stdout.write(f"  + O'qituvchi: {user.full_name} ({phone})")
        return teachers

    def _create_students(self, count):
        students = []
        used_phones = set()
        for i in range(count):
            phone = gen_phone()
            while phone in used_phones:
                phone = gen_phone()
            used_phones.add(phone)

            user = User.objects.create_user(
                username=phone,
                full_name=fake.name(),
                role=User.Role.STUDENT,
                phone=phone,
                email=fake.email(),
                password="student123",
            )
            student = Student.objects.create(
                user=user,
                birth_date=fake.date_of_birth(minimum_age=10, maximum_age=18),
                parent_name=fake.name(),
                parent_phone=gen_phone(),
                address=fake.address()[:255],
                note=random.choice(["", fake.sentence(), ""]),
            )
            students.append(student)
            self.stdout.write(f"  + O'quvchi: {user.full_name} ({phone})")
        return students

    def _create_groups(self, teachers, count):
        groups = []
        today = timezone.localdate()
        used_names = set()
        for i in range(count):
            name = random.choice(SUBJECTS)
            while name in used_names:
                name = f"{random.choice(SUBJECTS)} {random.randint(1, 99)}"
            used_names.add(name)

            start = today - timedelta(days=random.randint(30, 120))
            group = Group.objects.create(
                name=name,
                subject=random.choice(SUBJECTS),
                teacher=random.choice(teachers),
                monthly_price=Decimal(str(random.choice([300000, 400000, 500000, 600000, 750000]))),
                start_date=start,
                end_date=None,
                lesson_days=random.choice(LESSON_DAYS_OPTIONS),
                lesson_time=f"{random.choice([8, 9, 10, 14, 15, 16, 17])}:{random.choice(['00', '30'])}",
                room=random.choice(ROOMS),
                is_active=random.choices([True, False], weights=[0.85, 0.15])[0],
            )
            groups.append(group)
            self.stdout.write(f"  + Guruh: {group.name} ({group.teacher.full_name})")
        return groups

    def _create_enrollments(self, students, groups):
        enrollments = []
        active_groups = [g for g in groups if g.is_active]
        for student in students:
            assigned_groups = random.sample(
                active_groups,
                k=min(random.randint(1, 3), len(active_groups)),
            )
            for group in assigned_groups:
                start = group.start_date + timedelta(days=random.randint(0, 15))
                status = random.choices(
                    Enrollment.Status.choices,
                    weights=[0.75, 0.10, 0.10, 0.05],
                )[0][0]
                enrollment = Enrollment.objects.create(
                    student=student,
                    group=group,
                    start_date=start,
                    end_date=None if status in ("active", "paused") else start + timedelta(days=random.randint(30, 180)),
                    discount_percent=random.choices([0, 5, 10, 15, 20], weights=[60, 15, 10, 10, 5])[0],
                    status=status,
                )
                enrollments.append(enrollment)
        self.stdout.write(f"  + {len(enrollments)} ta yozilma yaratildi")
        return enrollments

    def _create_lessons(self, groups):
        lessons = []
        today = timezone.localdate()
        for group in groups:
            lesson_count = random.randint(5, 15)
            dates = set()
            while len(dates) < lesson_count:
                d = today - timedelta(days=random.randint(1, 90))
                if d >= group.start_date:
                    dates.add(d)

            for d in sorted(dates):
                is_held = random.choices([True, False], weights=[0.85, 0.15])[0]
                lesson = Lesson.objects.create(
                    group=group,
                    date=d,
                    topic=f"{group.subject}: {fake.sentence(nb_words=4)}",
                    is_held=is_held,
                    cancel_reason="" if is_held else fake.sentence(nb_words=3),
                    created_by=group.teacher,
                )
                lessons.append(lesson)
        self.stdout.write(f"  + {len(lessons)} ta dars yaratildi")
        return lessons

    def _create_attendance(self, lessons, enrollments):
        count = 0
        enrollment_map = {}
        for e in enrollments:
            key = (e.student_id, e.group_id)
            if e.status == Enrollment.Status.ACTIVE:
                enrollment_map[key] = e

        for lesson in lessons:
            active_students = [
                e.student for e in enrollments
                if e.group_id == lesson.group_id and e.status == Enrollment.Status.ACTIVE
            ]
            for student in active_students:
                if random.random() < 0.90:
                    status = random.choices(ATTENDANCE_STATUSES, weights=ATTENDANCE_WEIGHTS)[0]
                    Attendance.objects.create(
                        lesson=lesson,
                        student=student,
                        status=status,
                        comment="" if status == "present" else fake.sentence(nb_words=3),
                        marked_by=lesson.created_by,
                    )
                    count += 1
        self.stdout.write(f"  + {count} ta davomat yozildi")

    def _create_payments(self, enrollments):
        count = 0
        today = timezone.localdate()
        methods = ["cash", "card", "transfer"]

        for enrollment in enrollments:
            if enrollment.status in (Enrollment.Status.DROPPED, Enrollment.Status.FINISHED):
                continue
            months_active = max(1, (today - enrollment.start_date).days // 30)
            months_to_pay = random.randint(1, min(months_active, 6))
            for m in range(months_to_pay):
                period = (enrollment.start_date + timedelta(days=30 * m)).replace(day=1)
                if period > today:
                    break
                amount = enrollment.group.monthly_price * (Decimal("1") - Decimal(enrollment.discount_percent) / Decimal("100"))
                Payment.objects.create(
                    enrollment=enrollment,
                    amount=amount.quantize(Decimal("0.01")),
                    period=period,
                    paid_at=period + timedelta(days=random.randint(0, 10)),
                    method=random.choice(methods),
                    receipt_no=fake.bothify(text="???-#####").upper(),
                    created_by=enrollment.group.teacher,
                )
                count += 1
        self.stdout.write(f"  + {count} ta to'lov yaratildi")
