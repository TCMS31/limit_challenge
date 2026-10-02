from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from . import models


class BrokerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Broker
        fields = ["id", "name", "primary_contact_email"]


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Company
        fields = ["id", "legal_name", "industry", "headquarters_city"]


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TeamMember
        fields = ["id", "full_name", "email"]


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Contact
        fields = ["id", "name", "role", "email", "phone"]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Document
        fields = ["id", "title", "doc_type", "uploaded_at", "file_url"]


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Note
        fields = ["id", "author_name", "body", "created_at"]


class NoteSummarySerializer(serializers.Serializer):
    author_name = serializers.CharField(allow_null=True)
    body_preview = serializers.CharField()
    created_at = serializers.DateTimeField(allow_null=True)


class SubmissionListSerializer(serializers.ModelSerializer):
    broker = BrokerSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    owner = TeamMemberSerializer(read_only=True)
    document_count = serializers.IntegerField(read_only=True, default=0)
    note_count = serializers.IntegerField(read_only=True, default=0)
    latest_note = serializers.SerializerMethodField()

    class Meta:
        model = models.Submission
        fields = [
            "id",
            "status",
            "priority",
            "summary",
            "created_at",
            "updated_at",
            "broker",
            "company",
            "owner",
            "document_count",
            "note_count",
            "latest_note",
        ]

    @extend_schema_field(NoteSummarySerializer(allow_null=True))
    def get_latest_note(self, obj):
        author = getattr(obj, "latest_note_author", None)
        body = getattr(obj, "latest_note_body", None)
        created = getattr(obj, "latest_note_created_at", None)
        if not (author or body or created):
            return None
        preview = (body or "")[:200]
        return {
            "author_name": author,
            "body_preview": preview,
            "created_at": created,
        }


class SubmissionDetailSerializer(serializers.ModelSerializer):
    broker = BrokerSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    owner = TeamMemberSerializer(read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    notes = NoteSerializer(many=True, read_only=True)

    class Meta:
        model = models.Submission
        fields = [
            "id",
            "status",
            "priority",
            "summary",
            "created_at",
            "updated_at",
            "broker",
            "company",
            "owner",
            "contacts",
            "documents",
            "notes",
        ]
