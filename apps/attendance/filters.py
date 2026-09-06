import django_filters

from apps.attendance.models import Attendance


class AttendanceFilter(django_filters.FilterSet):
    student = django_filters.NumberFilter(field_name="student_id")
    group = django_filters.NumberFilter(field_name="lesson__group_id")
    date_from = django_filters.DateFilter(field_name="lesson__date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="lesson__date", lookup_expr="lte")

    class Meta:
        model = Attendance
        fields = ["student", "status", "group", "date_from", "date_to"]