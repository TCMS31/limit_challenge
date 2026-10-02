import django_filters
from django.db.models import Exists, OuterRef, Q

from submissions import models


class SubmissionFilterSet(django_filters.FilterSet):
    """List filters. Query params stay camelCase to match the frontend."""

    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    brokerId = django_filters.NumberFilter(field_name="broker_id")
    companySearch = django_filters.CharFilter(method="filter_company_search")
    createdFrom = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    createdTo = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    hasDocuments = django_filters.BooleanFilter(method="filter_has_documents")
    hasNotes = django_filters.BooleanFilter(method="filter_has_notes")

    class Meta:
        model = models.Submission
        fields = []

    def filter_company_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(company__legal_name__icontains=value) | Q(company__industry__icontains=value)
        )

    def filter_has_documents(self, queryset, name, value):
        return self._filter_has_related(queryset, models.Document, "has_documents", value)

    def filter_has_notes(self, queryset, name, value):
        return self._filter_has_related(queryset, models.Note, "has_notes", value)

    @staticmethod
    def _filter_has_related(queryset, related_model, alias, value):
        if value is None:
            return queryset
        related = Exists(related_model.objects.filter(submission_id=OuterRef("pk")))
        return queryset.alias(**{alias: related}).filter(**{alias: value})
