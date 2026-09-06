import django_filters

from apps.lessons.models import Lesson


class LessonFilter(django_filters.FilterSet):
    group = django_filters.NumberFilter(field_name="group_id")
    date_from = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Lesson
        fields = ["group", "date", "date_from", "date_to", "is_held"]