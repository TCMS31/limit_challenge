# Assumptions

These are the choices the solution is built on.

## Domain

- The app reviews submissions that already exist. It does not create, edit, or delete them.
- A broker is the outside firm that sent the opportunity. A company is who the deal is about. The owner is the internal team member tracking that submission.
- Contacts are people at the company for that one submission. They are not broker staff and they are not the owner.
- Documents store a title, a type, and a `fileUrl`. The seed uses `files.example` addresses. No file bytes are stored, so the UI does not download a real file.
- Notes are internal comments, newest first.
- A submission status is `new`, `in_review`, `closed`, or `lost`. Priority is `high`, `medium`, or `low`. The screen shows these labels. It does not change them.

## API

- JSON field names are camelCase. Query parameter names are camelCase too, because the camelCase renderer does not convert query params.
- The list is 10 rows per page, newest first.
- `companySearch` matches the company legal name or the industry. The gray text under a company name is that industry.
- `createdFrom` and `createdTo` include the whole calendar day, so the end date is included.
- `hasDocuments` and `hasNotes` are available on the API. The list screen does not show controls for them.
- `/api/brokers/` is a plain list for the dropdown, not a paginated page.
- CSV export uses the same filters as the list and includes every matching row, not only the page on screen. It is built with Python's `csv` module.

## Sign-in

- Every `/api/` route requires a bearer access token, except the docs. `/healthz/`, `/api/docs/`, `/api/redoc/`, and `/admin/` stay open.
- The access token lasts 15 minutes and stays in memory. The refresh token lasts one day in the httpOnly cookie `submission_refresh`. JavaScript cannot read that cookie.
- The seed account is `submission` / `submission-demo`. The seed creates that user even when the 25 submissions are already loaded.

## Dates and seed data

- The story dates start at 2025-11-01 15:00 UTC. `created_at` and note times use those dates.
- `updated_at` and document `uploaded_at` follow Django's automatic timestamps, so they show when the seed ran, not the story date.
- The seed is a fixed dataset. Running it again does nothing if submissions already exist. `--force` rebuilds the same rows.
- Docker Postgres and a local SQLite database are separate. Seeding one does not fill the other.

## Frontend

- The list URL is the source of truth for status, broker, company search, and page. A refresh and the back link keep those filters.
- Company search waits 300ms before it updates the URL.
- The list is treated as fresh for 30 seconds. The broker list is treated as fresh for 5 minutes.
- A missing submission is not retried. Other failed requests can be retried once.
- Dates on the detail page are shown in UTC so the server and the browser render the same text.
