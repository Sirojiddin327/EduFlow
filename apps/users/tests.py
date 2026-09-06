from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase


class PermissionTests(APITestCase):
    def setUp(self):
        from apps.users.models import User

        self.admin = User.objects.create_user(
            username="admin", password="admin123", phone="+998901000001",
            full_name="Admin", role=User.Role.ADMIN,
        )
        self.teacher = User.objects.create_user(
            username="teacher", password="teacher123", phone="+998901000002",
            full_name="Teacher", role=User.Role.TEACHER,
        )
        self.student = User.objects.create_user(
            username="student", password="student123", phone="+998901000011",
            full_name="Student", role=User.Role.STUDENT,
        )

    def _login(self, username, password):
        resp = self.client.post(
            "/api/auth/login/", {"username": username, "password": password}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return resp.data["access"]

    def _auth(self, username, password):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._login(username, password)}")

    def test_login_returns_jwt(self):
        resp = self.client.post(
            "/api/auth/login/", {"username": "admin", "password": "admin123"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_unauthenticated_gets_401(self):
        resp = self.client.get("/api/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_role(self):
        self._auth("admin", "admin123")
        resp = self.client.get("/api/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["role"], "admin")

    def test_student_cannot_create_group(self):
        from apps.users.models import User, Student

        self._auth("student", "student123")
        resp = self.client.post(
            "/api/groups/",
            {"name": "G", "subject": "Py", "teacher": self.teacher.id,
             "monthly_price": "100", "start_date": "2026-01-01",
             "lesson_days": "du", "lesson_time": "14:00", "room": "1"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_create_payment(self):
        from apps.groups.models import Group, Enrollment
        from apps.users.models import Student

        g = Group.objects.create(
            name="Py-1", subject="Py", teacher=self.teacher,
            monthly_price="100", start_date=date(2026, 1, 1),
            lesson_days="du", lesson_time="14:00", room="1",
        )
        s = Student.objects.create(user=self.student, birth_date=date(2010, 1, 1))
        e = Enrollment.objects.create(student=s, group=g, start_date=date(2026, 1, 1))

        self._auth("teacher", "teacher123")
        resp = self.client.post(
            "/api/payments/",
            {"enrollment": e.id, "amount": "100", "period": "2026-01-01",
             "paid_at": "2026-01-10", "method": "cash"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_sees_only_own_groups(self):
        from apps.users.models import User
        from apps.groups.models import Group

        other = User.objects.create_user(
            username="t2", password="x", phone="+998901000003",
            full_name="T2", role=User.Role.TEACHER,
        )
        Group.objects.create(
            name="Own", subject="Py", teacher=self.teacher,
            monthly_price="100", start_date=date(2026, 1, 1),
            lesson_days="du", lesson_time="14:00", room="1",
        )
        Group.objects.create(
            name="NotMine", subject="Py", teacher=other,
            monthly_price="100", start_date=date(2026, 1, 1),
            lesson_days="du", lesson_time="14:00", room="2",
        )
        self._auth("teacher", "teacher123")
        resp = self.client.get("/api/groups/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [g["name"] for g in resp.data["results"]]
        self.assertIn("Own", names)
        self.assertNotIn("NotMine", names)

    def test_student_cannot_see_others_student_card(self):
        from apps.users.models import User, Student

        other = User.objects.create_user(
            username="s2", password="x", phone="+998901000022",
            full_name="S2", role=User.Role.STUDENT,
        )
        s2 = Student.objects.create(user=other, birth_date=date(2010, 1, 1))

        self._auth("student", "student123")
        resp = self.client.get(f"/api/students/{s2.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)