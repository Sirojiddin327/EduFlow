from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.attendance.views import AttandanceViewSet

router = DefaultRouter()
router.register("", AttandanceViewSet, basename="attendance")

urlpatterns = [
    path("", include(router.urls)),
]