# EduFlow — O'quv markazi CRM

O'quv markazlari uchun CRM: guruhlar, o'quvchilar, davomat va to'lovlarni bitta bazada boshqaradi.
Administrator guruh ochadi va o'quvchini biriktiradi, o'qituvchi davomat belgilaydi, kassa to'lov kiritadi.
Tizim har bir o'quvchining qarzini avtomatik hisoblaydi va oy oxirida guruhlar bo'yicha hisobot beradi.

## Texnologiyalar

- Django 6.1 + Django REST Framework
- JWT autentifikatsiya — djangorestframework-simplejwt
- django-filter (filtrlash/qidiruv), PageNumberPagination
- PostgreSQL (SQLite faqat test/davr uchun fallback)
- aiogram 3 (Telegram bot — alohida `bot/` papkasida)

## O'rnatish

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# PostgreSQL sozlash (bir marta):
sudo apt install -y postgresql
sudo -u postgres createuser --superuser sirojiddin
sudo -u postgres psql -c "ALTER USER sirojiddin PASSWORD 'postgres';"
sudo -u postgres createdb eduflow

# .env ni yozing (.env.example ga qarang)
cp .env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Rollar

| Rol | Imkoniyatlar |
|-----|--------------|
| `admin` | Guruhlar, o'quvchilar, a'zoliklar, to'lovlar, hisobotlar, har qanday guruh ma'lumoti |
| `teacher` | Faqat o'z guruhlarini ko'radi, dars yaratadi va davomat belgilaydi; to'lov/qarzni ko'rmaydi (403) |
| `student` | Faqat o'z ma'lumotini ko'radi (o'qish rejadvali, davomat, qarz, to'lovlar) — o'zgartira olmaydi |

## Asosiy endpointlar

| Metod | Yo'l | Kim uchun |
|-------|------|-----------|
| POST | `/api/auth/login/` | hamma (JWT olish) |
| POST | `/api/auth/refresh/` | hamma |
| GET | `/api/me/` | hamma |
| GET/POST | `/api/groups/` | admin, teacher |
| PATCH/DELETE | `/api/groups/{id}/` | admin (DELETE — yopadi, o'chirmaydi) |
| GET/POST | `/api/students/`, `/api/students/{id}/` | admin, teacher; o'zi student |
| GET/POST | `/api/enrollments/` | admin, teacher |
| POST | `/api/enrollments/{id}/finish/` | admin |
| GET/POST | `/api/lessons/`, `/api/lessons/{id}/` | admin, teacher |
| GET/POST | `/api/lessons/{id}/attendance/` | admin, teacher (bulk belgilash) |
| GET | `/api/attendance/` | admin, teacher, student(o'zi) |
| GET/POST/DELETE | `/api/payments/` | admin; student(ro'yxat, o'zi) |
| GET | `/api/reports/debtors/` | admin |
| GET | `/api/reports/monthly/?year=&month=` | admin |
| GET | `/api/reports/student-debt/{id}/` | admin, student(o'zi) |
| GET | `/api/reports/attendance-summary/` | admin, teacher |
| POST | `/api/bot/link/` | `X-Bot-Token` |
| GET | `/api/bot/whoami/` | `X-Bot-Token` |

Filtrlash: `?is_active=...&teacher=...&subject=...`, qidiruv `?search=...`, tartiblash `?ordering=...`,
pagination `?page=2&page_size=50` (standart 20).

## Qarz hisobi

- Qarz **a'zolik (Enrollment)** darajasida: `expected - paid`.
- `expected` = oylar soni × `(monthly_price × (100 − discount_percent) / 100)`.
- Oylar soni SQL'da `ExtractYear/ExtractMonth` orqali: `(y2−y1)*12 + (m2−m1) + 1`, `end_date` bo'lmasa joriy oy.
- Bitta ORM so'rovda `annotate + Sum + Coalesce` — N+1 yo'q, `select_related` qo'shilgan.
- To'lov `period` doim oyning 1-sanasiga keltiriladi.
- **Ma'lum cheklov:** guruh `monthly_price` o'zgartirilsa, o'tgan oylar qayta hisoblanmaydi — hisobot yangi narx bilan chiqaveradi (spesifikatsiyadagi ataylab qilingan soddalashtirish).

## Testlar

```bash
# PostgreSQL o'rnatilmagan bo'lsa, sqlite bilan:
DB_ENGINE=django.db.backends.sqlite3 DB_NAME=/tmp/eduflow_test.sqlite python manage.py test apps.reports
python manage.py test apps.bot_api
```

Qarz hisobi uchun 4 ta asosiy test + debtors pagination, bot link FSM va impersonatsiya uchun 6 ta test.

## Bot

`bot/` papkasidagi aiogram 3 bot. Bot bazaga to'g'ridan-to'g'ri ulanmaydi — faqat API orqali.
Har bir so'rov `X-Bot-Token` + `X-Telegram-Id` bilan yuboriladi; server
`config/authentication.BotUserAuthentication` orqali so'rovni shu Telegram akkauntiga bog'langan
User sifatida tanitadi (rol cheklovlari API tomonda ishlaydi).

Oqimlar:

1. **Bog'lash** — `/start` → `whoami` bo'lmasa telefon so'raladi → `/api/bot/link/` kod (cache 5 min) → tasdiqlash.
2. **O'quvchi** — 💰 Mening qarzim, 🧾 to'lovlar tarixi, 📅 davomatim (30 kun, <70% ogohlantirish).
3. **O'qituvchi** — ✅ Davomat belgilash: guruh → kun (Bugun/Kecha/boshqa) → dars topish/yaratish →
   ⬜→✅→❌→🕐→📄 tugmalar bilan belgilash → bulk saqlash.
4. **Admin** — 📊 Qarzdorlar (sahifali, guruh tanlash), 🔄 yangilash, 📈 oylik hisobot.

### Botni ishga tushirish

```bash
# 1. .env da BOT_API_TOKEN (server bilan bir xil qiymat) va haqiqiy BOT_TOKEN yozilgan.
# 2. Django server ishlayapti: python manage.py runserver
# 3. Bot (alohida terminal):
source venv/bin/activate
python -m bot.main      # bot papkasidan: python main.py
```

`API_BASE_URL` (masalan `http://127.0.0.1:8000`) bot serverga ulanish yo'li.