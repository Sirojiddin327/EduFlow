from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.group_views import GroupViewSet, EnrollmentViewSet

router = DefaultRouter()
router.register("groups", GroupViewSet, basename="group")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")

urlpatterns = [
    path("", include(router.urls)),
]
