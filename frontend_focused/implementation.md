# Implementation

This is a read-only workspace for reviewing broker-submitted opportunities. An operator filters the list, opens one submission, and inspects the company, broker, owner, contacts, documents, and notes. The app does not create or edit records.

The domain diagram is in `docs/submission-flow.md`.

## How to run

Docker is the path for a new checkout. From this directory:

```bash
docker compose up --build
```

That starts Postgres, the API, and the Next.js dev server. On the first start the backend waits for the database, runs migrations, and loads the seed. Later starts keep the existing rows.

- App: `http://localhost:3000/submissions`
- API: `http://localhost:8000/api/submissions/`
- Swagger: `http://localhost:8000/api/docs/`

Use `localhost`, not `0.0.0.0`. The browser calls `http://localhost:8000/api`. Copy `.env.example` to `.env` only if you need to override the defaults.

Rebuild the same 25 submissions inside the running backend:

```bash
docker compose exec backend python manage.py seed_submissions --force
```

Without Docker, the API uses SQLite and the frontend is started separately.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_submissions
python manage.py runserver 0.0.0.0:8000
```

```bash
cd frontend
npm install
npm run dev
```

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000/api`. Set it in `frontend/.env.local` only to point somewhere else. The local SQLite database and the Docker Postgres database are separate.

The seed is a fixed dataset in `backend/submissions/seed_data.py`, anchored at 2025-11-01. Company search `Acme` returns five rows. The 2025-11-01 submission has no contacts, 2025-11-02 has no documents, and 2025-11-03 has no notes. The seed command does nothing when submissions already exist. `--force` deletes them and loads the same set again.

Backend tests:

```bash
cd backend
.venv/bin/python manage.py test submissions
```

## Must-haves

**List API.** `GET /api/submissions/` is paginated, 10 per page, newest first. Each row includes the company, broker, owner, document count, note count, and the latest note preview. The query uses `select_related` for company, broker, and owner, and annotates the counts and latest note so the list does not load every related row.

**Required filters.** `status`, `brokerId`, and `companySearch` are query params. `companySearch` is a case-insensitive match on the company legal name. Empty params are omitted. Unknown params are ignored.

**Detail API.** `GET /api/submissions/<id>/` returns the submission plus contacts, documents, and notes. That query uses `prefetch_related` for those three collections. A missing id returns 404.

**Brokers.** `GET /api/brokers/` returns a plain list for the dropdown, not a paginated wrapper.

**List screen.** `/submissions` keeps `status`, `brokerId`, `companySearch`, and `page` in the URL. Refreshing the page, sharing the link, and coming back from a detail page restore the same list. Company search is debounced by 300ms. The desktop layout is a table. Narrow screens use cards. The page shows how many rows are visible, and it has loading, empty, and error states. The previous page stays on screen while the next request is in flight.

**Detail screen.** `/submissions/[id]` shows the summary, status, priority, broker, owner, dates, contacts, documents, and notes. Empty sections say so. A failed request can be retried. An unknown id shows a not-found state. The back link keeps the list query string.

## Optional pieces

These are implemented beyond the three list filters:

- `createdFrom` and `createdTo` filter on the calendar date, so the end date is included.
- `hasDocuments` and `hasNotes` use an `Exists` check.
- Those four filters are on the API. The list screen exposes status, broker, and company search.
- Backend tests cover the filters, the list and detail shapes, a missing record, the broker list, and the OpenAPI schema.
- Docker Compose and the deterministic seed.
- Swagger UI at `/api/docs/` and ReDoc at `/api/redoc/`. The schema uses the same camelCase names as the JSON responses.

Authentication and deployment were left out.

## Approach

Query parameter names stay camelCase because the camelCase JSON renderer does not convert query params. Serializer fields are snake_case in Python and camelCase in the response. Swagger uses the same camelCase postprocessing hook, so the docs match the payload.

The URL is the source of truth for list state. React Query keys include the filters. The list is treated as fresh for 30 seconds. The broker dropdown is treated as fresh for 5 minutes. A 404 on a detail request is not retried.

Documents store a title, a type, and a `fileUrl`. The seed uses placeholder `files.example` addresses, so there is no file to download. `created_at` and note times come from the seed story. `updated_at` and document `uploaded_at` follow Django's automatic timestamps, so they show when the seed ran.

Backend code is copied into the Docker image, so backend changes need `docker compose up --build`. Frontend source is mounted into the frontend container, so frontend edits show up on refresh.
