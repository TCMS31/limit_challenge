import csv

from django.db.models import Count, OuterRef, Subquery
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action

from submissions import models, serializers
from submissions.filters.submission import SubmissionFilterSet

CSV_HEADERS = [
    "Company",
    "Industry",
    "Broker",
    "Owner",
    "Status",
    "Priority",
    "Documents",
    "Notes",
    "Latest note",
    "Created at",
]

STATUS_LABELS = {
    "new": "New",
    "in_review": "In Review",
    "closed": "Closed",
    "lost": "Lost",
}

PRIORITY_LABELS = {
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}


class SubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Submission.objects.all()
    filterset_class = SubmissionFilterSet

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("company", "broker", "owner")
            .order_by("-created_at")
        )

        if self.action in {"list", "export"}:
            latest_note = models.Note.objects.filter(submission_id=OuterRef("pk")).order_by(
                "-created_at"
            )
            return queryset.annotate(
                document_count=Count("documents", distinct=True),
                note_count=Count("notes", distinct=True),
                latest_note_author=Subquery(latest_note.values("author_name")[:1]),
                latest_note_body=Subquery(latest_note.values("body")[:1]),
                latest_note_created_at=Subquery(latest_note.values("created_at")[:1]),
            )

        return queryset.prefetch_related("contacts", "documents", "notes")

    @extend_schema(responses={(200, "text/csv"): bytes})
    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        submissions = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="submissions.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(CSV_HEADERS)
        for submission in submissions:
            latest_body = (getattr(submission, "latest_note_body", None) or "").replace("\n", " ")
            created = submission.created_at
            writer.writerow(
                [
                    submission.company.legal_name,
                    submission.company.industry,
                    submission.broker.name,
                    submission.owner.full_name,
                    STATUS_LABELS.get(submission.status, submission.status),
                    PRIORITY_LABELS.get(submission.priority, submission.priority),
                    submission.document_count,
                    submission.note_count,
                    latest_body[:200],
                    f"{created:%b} {created.day}, {created:%Y}",
                ]
            )
        return response

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.SubmissionListSerializer
        return serializers.SubmissionDetailSerializer


class BrokerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Broker.objects.all()
    serializer_class = serializers.BrokerSerializer
    pagination_class = None

