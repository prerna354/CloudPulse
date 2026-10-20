# CloudPulse

A distributed service-monitoring platform: it checks your services in the background, detects failures, raises alerts, and streams live updates to a dashboard.

## Overview
CloudPulse watches HTTP services (APIs, websites, internal tools). Background workers probe each service on a schedule, store the results, decide whether it is **up**, **degraded** or **down**, open alerts, and push the changes to every open browser instantly.

## Problem Statement
Teams often learn about outages from customers, not from their tools. Health data is scattered, checking by hand does not scale, and when something breaks it is hard to see what failed and when.

## Solution
Scheduled checks run in parallel on Celery workers, results are stored in PostgreSQL, hot data is cached in Redis, and WebSockets deliver live status to a React dashboard. A service is only declared *down* after 3 failed checks in a row, so one dropped request does not cause a false alarm.

## Key Features
- Scheduled, parallel health checks (Celery worker + beat)
- Failure detection: `up` / `degraded` (slow or first failure) / `down` (3 failures in a row)
- Automatic alerts that open on failure and resolve on recovery
- Real-time dashboard updates over WebSockets (Redis pub/sub bridges workers to the API)
- Redis caching of dashboard statistics
- JWT authentication, role-based access (admin / viewer), login rate limiting
- Search, status filter, pagination, response-time chart, confirmation dialogs, toasts
- Interactive API docs (Swagger) at `/docs`

## System Architecture
```
 React dashboard ──HTTP──▶ FastAPI ──▶ PostgreSQL
        ▲                     │  ▲
        │ WebSocket           │  └── Redis (cache + pub/sub)
        └──── FastAPI ◀───────┘            ▲
                                           │ publish events
 Celery beat ──every 15s──▶ Redis queue ──▶ Celery workers ──▶ probe services ──▶ PostgreSQL
```
1. **Celery beat** wakes up every 15 s and queues a check for each service that is due.
2. **Workers** probe the URL, save the result, update status, open/resolve alerts.
3. Workers **publish** an event to Redis; the API **forwards** it over WebSockets to the browser.

## Technology Stack
| Layer | Technology | Why |
|---|---|---|
| Frontend | React + Vite | Fast SPA, live UI |
| API | FastAPI, Pydantic | Typed validation, auto docs |
| Database | PostgreSQL (SQLite for quick local use), SQLAlchemy 2 | Relational history of checks |
| Background jobs | Celery + Redis | Parallel checks without blocking the API |
| Real time | WebSockets + Redis pub/sub | Instant dashboard updates |
| Packaging | Docker Compose | One-command run |

## Project Structure
```
cloudpulse/
├── backend/
│   ├── app/
│   │   ├── main.py            # app, CORS, error handlers, WebSocket
│   │   ├── models.py          # SQLAlchemy tables
│   │   ├── schemas.py         # request/response validation
│   │   ├── security.py        # password hashing, JWT
│   │   ├── routers/           # auth, services, alerts, dashboard, demo
│   │   ├── services/          # status_logic (pure), monitoring, ws_manager
│   │   ├── tasks/             # Celery app + check tasks
│   │   └── seed.py            # demo data
│   └── tests/
├── frontend/src/              # React app
├── docs/
├── docker-compose.yml
└── .env.example
```

## Database Design
- **users** (id, email UNIQUE, full_name, hashed_password, role, created_at)
- **monitored_services** (id, name UNIQUE, url, check_interval_seconds, timeout_ms, is_active, status INDEXED, consecutive_failures, last_checked_at, last_response_ms)
- **check_results** (id, service_id FK→services ON DELETE CASCADE, checked_at, is_up, status_code, response_ms, error) — composite index `(service_id, checked_at)`
- **alerts** (id, service_id FK→services ON DELETE CASCADE, severity, message, created_at, resolved_at, acknowledged) — index `(service_id, resolved_at)`

One service has many check results and many alerts.

## API Documentation
Full interactive docs: http://localhost:8000/docs. Auth = `Authorization: Bearer <token>`.

| Method | URL | Purpose | Auth | Errors |
|---|---|---|---|---|
| POST | `/api/auth/register` | Create a viewer account `{email, full_name, password}` | none | 409 duplicate, 422 invalid, 429 |
| POST | `/api/auth/login` | Get a token `{email, password}` | none | 401 wrong credentials, 429 |
| GET | `/api/auth/me` | Current user | any | 401 |
| GET | `/api/services?q=&status=&page=&page_size=` | List/search/filter services | any | 401, 422 |
| POST | `/api/services` | Add a service `{name, url, check_interval_seconds, timeout_ms}` | admin | 403, 409, 422 |
| GET | `/api/services/{id}` | One service | any | 404 |
| PATCH | `/api/services/{id}` | Edit a service | admin | 403, 404, 409 |
| DELETE | `/api/services/{id}` | Delete (204) | admin | 403, 404 |
| GET | `/api/services/{id}/results?limit=` | Recent checks | any | 404 |
| GET | `/api/alerts?active_only=&page=` | List alerts | any | 401 |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge | any | 404 |
| GET | `/api/dashboard/summary` | Counts, uptime, avg response (cached 5 s) | any | 401 |
| GET | `/api/health` | Liveness | none | |
| WS | `/ws?token=` | Live events | any | closes with 4401 if token invalid |
| GET | `/api/demo/{ok,slow,flaky,down}` | Built-in targets to monitor | none | |

## Authentication
Passwords are hashed with bcrypt. Login returns a signed JWT (HS256, 60 min). "Logout" removes the token in the browser. Admins can add/edit/delete services; viewers can only read.

## Installation
Requirements: Python 3.12, Node.js 20+, Git. Docker Desktop for the full stack (Redis + Postgres).

## Environment Variables
See `.env.example` (Docker) and `backend/.env.example` (no Docker). Never commit real `.env` files.

## Running Locally
**Option A, Docker (recommended: includes Redis, Celery, PostgreSQL)**
```bash
cp .env.example .env        # then edit the values
docker compose up --build
```
**Option B, without Docker (API + dashboard only):**
```bash
cd backend && python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # edit values
python -m app.seed
uvicorn app.main:app --reload
# new terminal
cd frontend && npm install && npm run dev
```
Without Redis there are no live background checks (they need the Celery worker + Redis), but you can browse the seeded data and use every page.

Open http://localhost:5173.

## Running with Docker
`docker compose up --build` builds the backend and frontend images, starts PostgreSQL and Redis, creates tables and demo data, then starts the API, a Celery worker, Celery beat and the dashboard.

## Testing
```bash
cd backend
python -m unittest tests.test_status_logic -v   # pure logic, no packages needed
pytest                                           # API + integration tests
```

## Sample Credentials
Created by the seed script using the passwords you put in `.env`:
- Admin: `admin@cloudpulse.dev` / value of `SEED_ADMIN_PASSWORD`
- Viewer: `viewer@cloudpulse.dev` / value of `SEED_VIEWER_PASSWORD`

## Screenshots
_Add screenshots of the dashboard, services page and alerts page here after running the project (save them in `docs/`)._

## Future Improvements
Alembic migrations, email/Slack notifications, per-service custom rules, data retention job, refresh tokens, CI pipeline.

## License
MIT
