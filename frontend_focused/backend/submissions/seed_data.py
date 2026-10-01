"""Fixed Submission Tracker dataset.

Every run produces the same brokers, companies, owners, and 25 submissions.
Dates are offsets from 2025-11-01 15:00 UTC, so createdFrom/createdTo checks
stay stable.

Handy lookups once seeded:

- Company search "Acme" matches Acme Industrial LLC and Acme Components Ltd.
- Company search "Health" matches Brightpath Health.
- Broker "Harbor & Co Brokerage" is the first broker.
- The earliest submission (Acme Industrial LLC, 2025-11-01) has no contacts.
- The 2025-11-02 submission (Northwind Logistics Inc) has no documents.
- The 2025-11-03 submission (Brightpath Health) has no notes.
"""

from datetime import datetime, timedelta, timezone

from submissions import models

ANCHOR = datetime(2025, 11, 1, 15, 0, tzinfo=timezone.utc)

BROKERS = [
    {"name": "Harbor & Co Brokerage", "primary_contact_email": "ops@harbor-co.example"},
    {"name": "Northwind Risk Partners", "primary_contact_email": "hello@northwind-risk.example"},
    {"name": "Summit Specialty Brokers", "primary_contact_email": "desk@summit-specialty.example"},
    {"name": "Lumen Commercial", "primary_contact_email": "submissions@lumen-commercial.example"},
    {"name": "Atlas Wholesale Brokers", "primary_contact_email": "team@atlas-wholesale.example"},
]

COMPANIES = [
    {"legal_name": "Acme Industrial LLC", "industry": "Manufacturing", "headquarters_city": "Chicago"},
    {"legal_name": "Northwind Logistics Inc", "industry": "Logistics", "headquarters_city": "Seattle"},
    {"legal_name": "Brightpath Health", "industry": "Healthcare", "headquarters_city": "Boston"},
    {"legal_name": "Cobalt Mining Co", "industry": "Mining", "headquarters_city": "Denver"},
    {"legal_name": "Delta Retail Group", "industry": "Retail", "headquarters_city": "Atlanta"},
    {"legal_name": "Evergreen Foods", "industry": "Food", "headquarters_city": "Portland"},
    {"legal_name": "Falcon Aerospace", "industry": "Aerospace", "headquarters_city": "Dallas"},
    {"legal_name": "Greenline Energy", "industry": "Energy", "headquarters_city": "Houston"},
    {"legal_name": "Helios Software", "industry": "Software", "headquarters_city": "Austin"},
    {"legal_name": "Iris Hospitality", "industry": "Hospitality", "headquarters_city": "Miami"},
    {"legal_name": "Juniper Financial", "industry": "Finance", "headquarters_city": "New York"},
    {"legal_name": "Acme Components Ltd", "industry": "Manufacturing", "headquarters_city": "Detroit"},
]

OWNERS = [
    {"full_name": "Avery Chen", "email": "avery.chen@limit.example"},
    {"full_name": "Jordan Patel", "email": "jordan.patel@limit.example"},
    {"full_name": "Morgan Ellis", "email": "morgan.ellis@limit.example"},
    {"full_name": "Riley Nguyen", "email": "riley.nguyen@limit.example"},
    {"full_name": "Samira Okonkwo", "email": "samira.okonkwo@limit.example"},
    {"full_name": "Taylor Brooks", "email": "taylor.brooks@limit.example"},
]

STATUSES = [
    models.Submission.Status.NEW,
    models.Submission.Status.IN_REVIEW,
    models.Submission.Status.CLOSED,
    models.Submission.Status.LOST,
]
PRIORITIES = [
    models.Submission.Priority.HIGH,
    models.Submission.Priority.MEDIUM,
    models.Submission.Priority.LOW,
]
DOC_TYPES = ["Summary", "Spreadsheet", "Presentation", "Contract"]

SUBMISSION_COUNT = 25
# Indexes into the generated submission list.
NO_CONTACTS_INDEX = 0
NO_DOCUMENTS_INDEX = 1
NO_NOTES_INDEX = 2


def create_seed_data():
    brokers = [models.Broker.objects.create(**row) for row in BROKERS]
    companies = [models.Company.objects.create(**row) for row in COMPANIES]
    owners = [models.TeamMember.objects.create(**row) for row in OWNERS]

    submissions = []
    for index in range(SUBMISSION_COUNT):
        company = companies[index % len(companies)]
        broker = brokers[index % len(brokers)]
        owner = owners[index % len(owners)]
        created_at = ANCHOR + timedelta(days=index)
        submissions.append(
            models.Submission(
                company=company,
                broker=broker,
                owner=owner,
                status=STATUSES[index % len(STATUSES)],
                priority=PRIORITIES[index % len(PRIORITIES)],
                summary=(
                    f"{company.legal_name} opportunity submitted by {broker.name}. "
                    f"Owner {owner.full_name} is tracking a "
                    f"{PRIORITIES[index % len(PRIORITIES)].label.lower()}-priority "
                    f"{STATUSES[index % len(STATUSES)].label.lower()} review."
                ),
                created_at=created_at,
                updated_at=created_at + timedelta(days=1),
            )
        )

    submissions = models.Submission.objects.bulk_create(submissions)

    contacts = []
    documents = []
    notes = []

    for index, submission in enumerate(submissions):
        if index != NO_CONTACTS_INDEX:
            for contact_number in (1, 2):
                contacts.append(
                    models.Contact(
                        submission=submission,
                        name=f"{submission.company.legal_name} Contact {contact_number}",
                        role="Operations" if contact_number == 1 else "Finance",
                        email=f"contact{contact_number}.s{index + 1}@example.com",
                        phone=f"+1-555-010-{index:02d}{contact_number}",
                    )
                )

        if index != NO_DOCUMENTS_INDEX:
            for doc_number in (1, 2):
                documents.append(
                    models.Document(
                        submission=submission,
                        title=f"{submission.company.legal_name} {DOC_TYPES[(index + doc_number) % len(DOC_TYPES)]}",
                        doc_type=DOC_TYPES[(index + doc_number) % len(DOC_TYPES)],
                        file_url=f"https://files.example/submissions/{index + 1}/doc-{doc_number}",
                        uploaded_at=submission.created_at + timedelta(hours=6 * doc_number),
                    )
                )

        if index != NO_NOTES_INDEX:
            notes.append(
                models.Note(
                    submission=submission,
                    author_name=submission.owner.full_name,
                    body=(
                        f"Opened the {submission.company.legal_name} file and assigned "
                        f"it to {submission.owner.full_name}."
                    ),
                    created_at=submission.created_at + timedelta(hours=4),
                )
            )
            notes.append(
                models.Note(
                    submission=submission,
                    author_name=submission.owner.full_name,
                    body=(
                        f"Latest update on {submission.company.legal_name}: status is "
                        f"{submission.get_status_display()}."
                    ),
                    created_at=submission.created_at + timedelta(hours=30),
                )
            )

    models.Contact.objects.bulk_create(contacts)
    models.Document.objects.bulk_create(documents)
    models.Note.objects.bulk_create(notes)

    return {
        "submissions": len(submissions),
        "contacts": len(contacts),
        "documents": len(documents),
        "notes": len(notes),
    }
