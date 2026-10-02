import json
from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from submissions import models


class SubmissionApiTests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="submission", password="submission-demo")
        self.client.force_authenticate(user=user)
        self.harbor = models.Broker.objects.create(
            name="Harbor & Co Brokerage",
            primary_contact_email="ops@harbor-co.example",
        )
        self.summit = models.Broker.objects.create(
            name="Summit Specialty Brokers",
            primary_contact_email="desk@summit-specialty.example",
        )
        self.acme = models.Company.objects.create(
            legal_name="Acme Industrial LLC",
            industry="Manufacturing",
            headquarters_city="Chicago",
        )
        self.acme_components = models.Company.objects.create(
            legal_name="Acme Components Ltd",
            industry="Manufacturing",
            headquarters_city="Detroit",
        )
        self.health = models.Company.objects.create(
            legal_name="Brightpath Health",
            industry="Healthcare",
            headquarters_city="Boston",
        )
        self.owner = models.TeamMember.objects.create(
            full_name="Avery Chen",
            email="avery.chen@limit.example",
        )

        self.with_files = self._submission(
            company=self.acme,
            broker=self.harbor,
            submission_status=models.Submission.Status.NEW,
            created_at=datetime(2025, 11, 1, 15, 0, tzinfo=timezone.utc),
        )
        models.Document.objects.create(
            submission=self.with_files,
            title="Acme Contract",
            doc_type="Contract",
            file_url="https://files.example/acme",
        )
        models.Note.objects.create(
            submission=self.with_files,
            author_name=self.owner.full_name,
            body="Opened the Acme file.",
            created_at=self.with_files.created_at + timedelta(hours=4),
        )

        self.no_documents = self._submission(
            company=self.acme_components,
            broker=self.harbor,
            submission_status=models.Submission.Status.IN_REVIEW,
            created_at=datetime(2025, 11, 2, 15, 0, tzinfo=timezone.utc),
        )
        models.Note.objects.create(
            submission=self.no_documents,
            author_name=self.owner.full_name,
            body="No documents yet.",
            created_at=self.no_documents.created_at + timedelta(hours=4),
        )

        self.no_notes = self._submission(
            company=self.health,
            broker=self.summit,
            submission_status=models.Submission.Status.CLOSED,
            created_at=datetime(2025, 11, 10, 15, 0, tzinfo=timezone.utc),
        )
        models.Document.objects.create(
            submission=self.no_notes,
            title="Health Summary",
            doc_type="Summary",
            file_url="https://files.example/health",
        )
        models.Contact.objects.create(
            submission=self.no_notes,
            name="Brightpath Health Contact 1",
            role="Operations",
            email="contact1@example.com",
        )

    def _submission(self, company, broker, submission_status, created_at):
        return models.Submission.objects.create(
            company=company,
            broker=broker,
            owner=self.owner,
            status=submission_status,
            priority=models.Submission.Priority.HIGH,
            summary=f"{company.legal_name} opportunity",
            created_at=created_at,
        )

    def _payload(self, response):
        return json.loads(response.content)

    def _ids(self, response):
        return {row["id"] for row in self._payload(response)["results"]}

    def test_status_filter(self):
        response = self.client.get(reverse("submission-list"), {"status": "in_review"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response), {self.no_documents.id})

    def test_broker_filter(self):
        response = self.client.get(reverse("submission-list"), {"brokerId": self.harbor.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response), {self.with_files.id, self.no_documents.id})

    def test_company_search_matches_partial_name(self):
        response = self.client.get(reverse("submission-list"), {"companySearch": "acme"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response), {self.with_files.id, self.no_documents.id})

    def test_export_csv_respects_company_search(self):
        response = self.client.get("/api/submissions/export/", {"companySearch": "manufacturing"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", response["Content-Type"])
        body = response.content.decode()
        self.assertIn("Acme Industrial LLC", body)
        self.assertIn("Acme Components Ltd", body)
        self.assertIn("Created at", body)
        self.assertIn("Nov 1, 2025", body)
        self.assertNotIn("Brightpath Health", body)

    def test_company_search_matches_industry(self):
        response = self.client.get(reverse("submission-list"), {"companySearch": "manufacturing"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response), {self.with_files.id, self.no_documents.id})

    def test_created_range_includes_the_end_date(self):
        response = self.client.get(
            reverse("submission-list"),
            {"createdFrom": "2025-11-02", "createdTo": "2025-11-02"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self._ids(response), {self.no_documents.id})

    def test_has_documents_and_notes_false(self):
        no_documents = self.client.get(reverse("submission-list"), {"hasDocuments": "false"})
        no_notes = self.client.get(reverse("submission-list"), {"hasNotes": "false"})

        self.assertEqual(self._ids(no_documents), {self.no_documents.id})
        self.assertEqual(self._ids(no_notes), {self.no_notes.id})

    def test_list_includes_counts_and_latest_note(self):
        response = self.client.get(reverse("submission-list"), {"status": "new"})

        row = self._payload(response)["results"][0]
        self.assertEqual(row["documentCount"], 1)
        self.assertEqual(row["noteCount"], 1)
        self.assertEqual(row["latestNote"]["bodyPreview"], "Opened the Acme file.")
        self.assertEqual(row["company"]["legalName"], "Acme Industrial LLC")

    def test_detail_includes_related_records(self):
        response = self.client.get(reverse("submission-detail", args=[self.no_notes.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = self._payload(response)
        self.assertEqual(len(payload["contacts"]), 1)
        self.assertEqual(payload["documents"][0]["title"], "Health Summary")
        self.assertEqual(payload["notes"], [])

    def test_detail_missing_submission_is_404(self):
        response = self.client.get(reverse("submission-detail", args=[99999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_broker_list_is_not_paginated(self):
        response = self.client.get(reverse("broker-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = self._payload(response)
        self.assertIsInstance(payload, list)
        self.assertEqual(
            [broker["name"] for broker in payload],
            ["Harbor & Co Brokerage", "Summit Specialty Brokers"],
        )


class ApiDocsTests(APITestCase):
    def test_openapi_schema_uses_camel_case(self):
        response = self.client.get("/api/schema/?format=json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema = response.content.decode()
        self.assertIn("companySearch", schema)
        self.assertIn("legalName", schema)

    def test_swagger_ui_is_available(self):
        response = self.client.get("/api/docs/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AuthenticationTests(APITestCase):
    def setUp(self):
        get_user_model().objects.create_user(username="submission", password="submission-demo")

    def test_submissions_require_a_token(self):
        response = self.client.get("/api/submissions/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_health_and_docs_stay_public(self):
        health = self.client.get("/healthz/")
        docs = self.client.get("/api/docs/")

        self.assertEqual(health.status_code, status.HTTP_200_OK)
        self.assertEqual(docs.status_code, status.HTTP_200_OK)

    def test_login_puts_refresh_in_a_cookie(self):
        response = self.client.post(
            "/api/auth/token/",
            {"username": "submission", "password": "submission-demo"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertIn("submission_refresh", response.cookies)
        self.assertTrue(response.cookies["submission_refresh"]["httponly"])

    def test_refresh_rotates_the_cookie_and_logout_clears_it(self):
        login = self.client.post(
            "/api/auth/token/",
            {"username": "submission", "password": "submission-demo"},
            format="json",
        )
        first_refresh = login.cookies["submission_refresh"].value

        refreshed = self.client.post("/api/auth/token/refresh/")

        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        self.assertIn("access", refreshed.data)
        self.assertNotIn("refresh", refreshed.data)
        rotated = refreshed.cookies["submission_refresh"].value
        self.assertNotEqual(rotated, first_refresh)

        self.client.cookies["submission_refresh"] = first_refresh
        reused = self.client.post("/api/auth/token/refresh/")
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.cookies["submission_refresh"] = rotated
        logout = self.client.post("/api/auth/logout/")
        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(logout.cookies["submission_refresh"].value, "")
