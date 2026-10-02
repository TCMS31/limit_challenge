# Fleet Maintenance API

REST API for a company that assigns vehicles to offices and tracks the maintenance mechanics perform on them. Built with Django, Django REST Framework, and PostgreSQL. A Next.js frontend covers the day-to-day vehicle workflow.

The challenge text stays in `README.md`. This file is the implementation write-up: what was built for each requirement, how to run it, how to test it, assumptions, and tradeoffs.

The API lives at `http://localhost:8000/api/`. List endpoints are paginated at 10 rows (`count`, `next`, `previous`, `results`). Office summary and mechanic workload return a plain list, matching the shapes in the challenge.

## Requirements and implementation

### Domain

| Requirement | Implementation |
| --- | --- |
| Offices have a name and a city | `Office` model. CRUD at `/api/offices/`. |
| Vehicles have VIN, license plate, make, model, year, office, and an active flag | `Vehicle` model. CRUD at `/api/vehicles/`. |
| A VIN identifies one vehicle | `vin` is unique. A duplicate returns 400 with a field error. |
| Two active vehicles cannot share a license plate | Partial unique constraint on `license_plate` where `is_active` is true. An inactive vehicle may keep a plate that an active vehicle uses. |
| Mechanics have a name, certification number, and an active flag | `Mechanic` model. Certification numbers are unique. CRUD at `/api/mechanics/`. |
| Maintenance records link a vehicle and a mechanic, with a date, type, cost, and notes | `MaintenanceRecord` model. Cost cannot be negative. CRUD at `/api/maintenance-records/`. |
| A vehicle has many records, a mechanic services many vehicles, an office has many vehicles | Foreign keys with `on_delete=PROTECT`, so a row that is still referenced cannot be deleted. The API returns 400 in that case. |

Maintenance type is one of `oil_change`, `inspection`, `repair`, or `tires`. The challenge left the type open, so these four cover the jobs a fleet shop actually records.

### Endpoints

| Requirement | Method and path |
| --- | --- |
| CRUD for offices, vehicles, mechanics, and maintenance records | `GET/POST /api/offices/`, `/api/vehicles/`, `/api/mechanics/`, `/api/maintenance-records/` and `GET/PUT/PATCH/DELETE` on `/{id}/` |
| Office summary: active vehicle count, maintenance cost for the last 12 months, latest maintenance date | `GET /api/offices/summary/` |
| Vehicle search by any combination of office, active flag, make, model, maintenance dates, and mechanic certification | `GET /api/vehicles/search/` |
| Vehicle detail with office, full history, and the mechanic on each record | `GET /api/vehicles/{id}/` |
| Maintenance history for one vehicle, newest first | `GET /api/vehicles/{id}/maintenance/` |
| Move a vehicle to another office, changing only the office | `POST /api/vehicles/{id}/assign/` with `{ "office": <id> }` |
| Mechanic workload for the current calendar year, busiest first | `GET /api/mechanics/workload/` |
| Active vehicles that were never serviced, or whose last service was more than 365 days ago, oldest first | `GET /api/vehicles/needs-maintenance/` |
| Duplicate check for a VIN and license plate, naming the conflicting fields | `GET /api/vehicles/check-duplicate/?vin=&license_plate=&exclude=` |

Search query parameters, all optional: `office`, `active`, `make`, `model`, `maintained_after`, `maintained_before`, `certification_number`. Make and model match any case-insensitive fragment, so `toy` finds `Toyota`. A date range and a certification number must match the same maintenance row.

Office summary cost is a rolling 365 days, not the calendar year. Workload is the current calendar year. Needs-maintenance lists never-serviced vehicles before overdue ones.

Invalid input returns 400 with field messages. Unknown ids return 404.

### Frontend

The challenge asks for a React UI that uses the CRUD endpoints, vehicle search, and one other endpoint.

| Screen | What it calls |
| --- | --- |
| `/login` | `POST /api/auth/token/` |
| `/` | Vehicle search, plus create and edit |
| `/vehicles/{id}` | Vehicle detail, edit, and assign to another office |
| `/needs-maintenance` | Vehicles needing maintenance |

Filters for office, active status, and maintenance dates update the URL immediately. Make, model, and certification apply when you submit the form, so the query string stays shareable. Loading, empty, and error states are on each screen.

The UI does not create offices, mechanics, or maintenance records, and it has no delete button. Those operations are on the API and in Django admin.

### Seed data

`python manage.py seed_fleet` fills the database with Faker. Defaults: 8 offices, 150 vehicles, 25 mechanics, and one vehicle with 400 maintenance records so the detail endpoint can be checked under load. `--seed 42` keeps names stable. `--clear` wipes fleet rows and reloads them. The command refuses to run when fleet rows already exist unless `--clear` is passed.

It also creates the API user `fleet` / `fleet-demo`. That user is not a Django staff user.

### Tests

`fleet/tests.py` covers duplicate VIN, the active-only plate rule, assign, the duplicate check, needs-maintenance order, calendar-year workload, the rolling office summary, combined search, a negative cost, the vehicle detail query count, and JWT (a missing token, the public health check, a bad password, a create with a valid access token, refresh from the cookie, and logout blacklisting that cookie).

## Extra work

These pieces are outside the challenge checklist.

| Extra | What it does |
| --- | --- |
| Docker Compose | Postgres 16, the Django API, and the Next.js app. The backend waits for Postgres, then migrates, on startup. |
| `GET /healthz/` | Public liveness check. It does not require a token. |
| JWT | Optional in the challenge. Documented in the next section. |
| Django admin | Unfold theme at `/admin/`. Staff only. The home page charts active vehicles by office, maintenance cost over the same rolling year as the office summary, and the ten busiest mechanics this year. The model list and recent actions stay on that page. |
| SQLite fallback | If `POSTGRES_HOST` is unset, Django uses SQLite so `runserver` works without Compose. |

### JWT

Authentication uses `djangorestframework-simplejwt`. Every `/api/` route requires a bearer access token. `/healthz/` and `/admin/` do not. Admin uses Django's own staff session.

| Token | Lifetime | Where it lives |
| --- | --- | --- |
| Access | 15 minutes | Memory in the browser. Sent as `Authorization: Bearer`. A reload drops it. |
| Refresh | 1 day | `httpOnly` cookie `fleet_refresh`. JavaScript cannot read it. `SameSite=Lax`, path `/api/auth/`. `Secure` is on when `DEBUG` is off. |

| Request | What it does |
| --- | --- |
| `POST /api/auth/token/` | Body is username and password. The JSON response contains only `access`. The refresh token is set as the cookie. |
| `POST /api/auth/token/refresh/` | No token in the body. The browser sends the cookie. The response is a new access token, and the cookie is replaced with a new refresh token. The previous refresh token is blacklisted. |
| `POST /api/auth/logout/` | Blacklists the refresh token from the cookie and clears the cookie. |

On load, the frontend calls refresh with credentials. If the cookie is still valid, the user stays signed in and receives a new access token. If refresh fails, the app goes to `/login`. API calls that get a 401 try that refresh once before giving up. The axios client uses `withCredentials`, and Django has `CORS_ALLOW_CREDENTIALS` so the browser will store and send the cookie from `localhost:3000` to `localhost:8000`.

The demo user is `fleet` / `fleet-demo`, created by `seed_fleet`. That user is not staff, so it cannot open `/admin/`.

## How to run

### Docker

From this directory:

```bash
docker compose up --build
```

- API health check: `http://localhost:8000/healthz/`
- API root: `http://localhost:8000/api/`
- Frontend: `http://localhost:3000`
- Admin: `http://localhost:8000/admin/`
- Postgres: `localhost:5432` (database, user, and password default to `fleet`)

Then load sample data and sign in to the UI as `fleet` / `fleet-demo`:

```bash
docker compose exec backend python manage.py seed_fleet --clear
```

Admin needs a staff user. The seed user cannot open `/admin/`.

```bash
docker compose exec backend python manage.py createsuperuser
```

Source directories are bind-mounted, so code edits apply without a rebuild. Rebuild after changing `backend/requirements.txt` or `frontend/package-lock.json`.

Copy `.env.example` to `.env` to override ports, the Django secret, or the API URL the browser calls (`NEXT_PUBLIC_API_BASE_URL`). That URL must stay on `localhost` from the browser's point of view, not the Compose service name.

Port 5432 is published as 5432. Stop any local Postgres that is already bound to that port before `docker compose up`.

### Without Docker

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_fleet
python manage.py runserver 0.0.0.0:8000
```

Frontend, in another shell:

```bash
cd frontend
npm install
npm run dev
```

`NEXT_PUBLIC_API_BASE_URL` defaults to `http://localhost:8000/api`.

## How to run tests

With Compose:

```bash
docker compose exec backend python manage.py test fleet
```

From the backend virtualenv:

```bash
cd backend
python manage.py test fleet
```

Tests use Django's test database. They do not write to the Compose database you use in the browser.

## Assumptions

- Maintenance type is `oil_change`, `inspection`, `repair`, or `tires`.
- "Last 12 months" on the office summary, and on the admin cost chart, is a rolling 365 days ending today.
- Mechanic workload uses the current calendar year, from January 1 through today.
- A license plate is unique only among active vehicles. Inactive vehicles may share one.
- Deleting an office, vehicle, or mechanic that still has related rows is rejected. Remove or reassign those rows first.
- Make and model search matches a case-insensitive fragment, because those filters are free-text boxes.
- The API requires JWT even though the challenge said authentication was unnecessary. `/healthz/` stays public.
- The demo API user is created by `seed_fleet`

## Tradeoffs

- Summary and workload are unpaginated lists because the challenge examples are a single array. Search, needs-maintenance, and the CRUD lists are paginated so a large fleet stays usable.
- Office summary uses correlated subqueries instead of joins, so vehicle and maintenance rows cannot multiply the cost.
- Vehicle detail prefetches the office and the maintenance history (with each mechanic) so a vehicle with hundreds of records stays a small, fixed number of queries.
- Assign updates only `office`. It does not write a history of past offices.
- The access token stays in memory and the refresh token stays in an `httpOnly` cookie. A reload can sign the user back in, and page JavaScript cannot read the long-lived token.
- Access tokens last 15 minutes and each refresh rotates the refresh token. That limits how long a stolen access token works, at the cost of an extra refresh request.
- The admin charts read the same query helpers as the API. They are a staff view of data the API already computes, not a second reporting path.
