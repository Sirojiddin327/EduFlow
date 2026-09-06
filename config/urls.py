from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.groups.urls")),
    path("api/lessons/", include("apps.lessons.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/bot/", include("apps.bot_api.urls")),
]
