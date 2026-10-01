from django.core.management.base import BaseCommand
from django.db import transaction

from submissions import models
from submissions.seed_data import create_seed_data


class Command(BaseCommand):
    help = "Seed a fixed Submission Tracker dataset for local testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Clear existing submissions data before seeding",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if models.Submission.objects.exists():
                if not options["force"]:
                    self.stdout.write(
                        self.style.WARNING(
                            "Submissions already exist; rerun with --force to rebuild seed data."
                        )
                    )
                    return
                self.stdout.write("Clearing existing submissions data...")
                models.Note.objects.all().delete()
                models.Document.objects.all().delete()
                models.Contact.objects.all().delete()
                models.Submission.objects.all().delete()
                models.Broker.objects.all().delete()
                models.Company.objects.all().delete()
                models.TeamMember.objects.all().delete()

            counts = create_seed_data()

        self.stdout.write(
            self.style.SUCCESS(
                "Seed data created: "
                f"{counts['submissions']} submissions, "
                f"{counts['contacts']} contacts, "
                f"{counts['documents']} documents, "
                f"{counts['notes']} notes."
            )
        )
