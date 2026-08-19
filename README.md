# Business Internship Aggregator

## Live Application

| | URL |
|---|---|
| Frontend | https://business-internship-aggregator.vercel.app |
| Backend API | https://business-internship-aggregator-api.onrender.com |
| API Docs (Swagger) | https://business-internship-aggregator-api.onrender.com/docs |

The backend runs on Render's free tier, which spins down after ~15 minutes of inactivity — the first request after a quiet period can take 30-50 seconds while it cold-starts. Subsequent requests are fast.

## Overview

Business Internship Aggregator is an in-progress platform that automatically discovers and aggregates business-related internship opportunities from company career websites, presenting them in one searchable interface. It is being built as both a portfolio project and a genuinely useful tool for business students.

## Problem

Business students looking for internships in Product Management, Business Analytics, Finance, Accounting, Consulting, Marketing, Operations, Supply Chain, Strategy, or Human Resources have to manually check dozens of individual company career pages, since opportunities are scattered with no central source. Most existing internship aggregators are built for and optimized around software engineering roles, leaving business students underserved.

## Solution

An automated pipeline that scrapes company career pages for business-relevant internships, normalizes and deduplicates the data, stores it in a central database, and exposes it through a searchable, filterable web interface — kept up to date without requiring students to check each company site individually.

## Current Status

**Deployed to production, scraping 8 real companies across 2 ATS platforms (Phases 1–7 complete).** PostgreSQL schema, SQLAlchemy models, and Alembic migrations are implemented and tested. A read-only FastAPI backend (search, filtering, pagination, sorting) is implemented and tested against live data. A Next.js (App Router, TypeScript, Tailwind) frontend consumes that API — search, filters, sorting, pagination, internship and company detail pages. The scraper runs on a schedule via GitHub Actions against a managed production database (see "Live Application" and "Production" below). See `docs/roadmap.md` for the full phase-by-phase build order.

## Supported ATS Platforms & Companies

| ATS | Companies |
|---|---|
| Greenhouse | Robinhood, Cloudflare, Braze, Rocket Lab, SpaceX, Red Ventures, SpotHopper |
| Workday | Abbott Laboratories |

Both integrations share the same `BaseScraper` lifecycle (company lookup, dedup, insert/update, inactive-lifecycle handling, per-listing error isolation, scraper-run metrics). A company only ever needs a small config file under `scrapers/companies/` — see "Scraper Architecture" in `docs/architecture.md`.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Scraping | Python, `requests` (both current ATS integrations expose public JSON APIs; Playwright remains a dependency for a future non-API ATS, per `docs/roadmap.md`) |
| Automation | GitHub Actions |
| Testing | pytest |
| Version Control | Git + GitHub |

This stack is intentionally kept simple and appropriate for a student-built MVP — no Kubernetes, microservices, or big-data infrastructure.

## Architecture

```text
Company Career Websites
        ↓
     Playwright
        ↓
 Company Scrapers
        ↓
 Data Normalization
        ↓
 Duplicate Detection
        ↓
    PostgreSQL
        ↓
     FastAPI
        ↓
     Next.js
        ↓
       User
```

Full details, including component responsibilities and data flow, are documented in [`docs/architecture.md`](docs/architecture.md).

## Local Development

Requires PostgreSQL, Python 3.12+, and Node.js 20.9+ (LTS) installed locally.

**Environment variables** — copy `.env.example` to `.env` (backend) and `frontend/.env.example` to `frontend/.env.local` (frontend):

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | `.env` | PostgreSQL connection string |
| `CORS_ALLOWED_ORIGINS` | `.env` | Origins allowed to call the API (default `http://localhost:3000`) |
| `NEXT_PUBLIC_API_BASE_URL` | `frontend/.env.local` | Base URL the frontend calls (default `http://localhost:8000`) |

**Terminal 1 — PostgreSQL**: start the `postgresql-x64-16` Windows service (or however it's installed locally), and make sure the `business_internships` database exists.

**Terminal 2 — FastAPI backend**:
```
py -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m uvicorn backend.api.main:app --reload
```
API docs: `http://127.0.0.1:8000/docs` (Swagger) or `http://127.0.0.1:8000/redoc`.

To populate real data, run a scraper directly, e.g. `.\.venv\Scripts\python -m scrapers.companies.robinhood`.

**Terminal 3 — Next.js frontend**:
```
cd frontend
npm install
npm run dev
```
App: `http://localhost:3000`.

Example API requests:
```
GET /internships?search=marketing&category=Marketing&page=1&page_size=10
GET /internships?company=Cloudflare&location=London&active=true
GET /internships/12
GET /companies
GET /companies/6
GET /categories
```

**Running tests** (requires the local PostgreSQL setup above — tests run against the local dev database and clean up their own `test-`-prefixed data; external HTTP calls are mocked, so no scraper test depends on a real career site):
```
.\.venv\Scripts\python -m pytest tests/ -v
```

## Production

```text
Career Sites
     ↓
  Scrapers
     ↓
GitHub Actions (scheduled + manual)
     ↓
Managed PostgreSQL (Neon)
     ↓
   FastAPI (Render)
     ↓
   Next.js (Vercel)
     ↓
    User
```

| Layer | Provider | Notes |
|---|---|---|
| Database | [Neon](https://neon.tech) | Managed serverless Postgres, free tier. Schema created via `alembic upgrade head`, never manual DDL. |
| Backend | [Render](https://render.com) | Free Web Service, deployed via `render.yaml` (Blueprint). Start command runs `alembic upgrade head` before `uvicorn` on every deploy, so schema changes ship automatically. No `--reload`, no debug mode. |
| Frontend | [Vercel](https://vercel.com) | Auto-deploys `frontend/` on push to `main`. |
| Scraper automation | GitHub Actions (`.github/workflows/scraper.yml`) | Runs on a 6-hour schedule and via manual `workflow_dispatch`. Applies migrations, then runs `python -m scrapers.scheduler`, which runs every company scraper with per-company error isolation. |

**Environment separation**: local development uses `.env` (backend) / `frontend/.env.local` (frontend), both gitignored and never committed. Production configuration lives entirely in Render's environment variables, Vercel's environment variables, and GitHub Actions repository secrets — never in source. `DATABASE_URL` in particular is a GitHub Actions secret (used by the scraper workflow) and a Render environment variable (used by the API) — the two are separate configuration surfaces pointing at the same managed database, and neither value is ever logged or committed.

**CORS**: `CORS_ALLOWED_ORIGINS` on Render is a comma-separated allowlist (currently local dev + the production Vercel URL) — never a wildcard.

## Planned MVP Features

- Automated internship collection from company career sites
- Data normalization into a consistent schema
- PostgreSQL storage
- Duplicate detection
- Basic REST API (search, filter, pagination)
- Searchable web interface with basic filtering

User accounts, AI resume matching, personalized recommendations, notifications, application tracking, and advanced analytics are explicitly **out of scope** for the MVP — see [`docs/PRD.md`](docs/PRD.md) for full scope and rationale.

## Roadmap

Development proceeds in phases, from foundation → database → scraping MVP → backend → frontend → multi-company scraping → automation → product features → intelligence (AI). Full phase-by-phase detail, including goals and definitions of done, is in [`docs/roadmap.md`](docs/roadmap.md).

## Future Vision

Beyond the MVP, the long-term goal is to become a broader internship discovery and career intelligence platform for business students — including user accounts, saved searches, email alerts, application tracking, resume matching, AI-powered recommendations, and hiring trend analytics.

## Repository Structure

```text
business-internship-aggregator/
│
├── frontend/
│   ├── app/            # Next.js App Router pages (home, internship/company detail)
│   ├── components/     # Reusable UI components
│   └── lib/             # Typed API client + shared types
├── backend/
│   ├── api/           # FastAPI app, routes, response schemas
│   ├── models/         # SQLAlchemy models
│   └── database/       # DB session, dedupe-key utils, seed data
├── scrapers/
│   ├── companies/      # Per-company scraper configs (see "Supported ATS Platforms" above)
│   ├── base_scraper.py     # Shared DB/lifecycle/metrics logic for every ATS
│   ├── greenhouse.py       # Shared Greenhouse ATS fetch/parse logic
│   ├── workday.py          # Shared Workday ATS fetch/parse logic
│   ├── classification.py   # Title -> category classification
│   ├── schemas.py          # NormalizedInternship + pre-insert validation
│   ├── http_utils.py       # Shared retry/backoff HTTP session
│   ├── text_utils.py       # Shared HTML/date/location cleanup
│   └── scheduler.py        # Runs all company scrapers (invoked by GitHub Actions)
├── database/           # database/schema.sql (source-of-truth DDL)
├── alembic/             # Migrations
├── tests/               # pytest suite (classification, dedupe, lifecycle, metrics, scheduler)
├── docs/                # Product and technical documentation
└── README.md
```

## Documentation

- [Product Requirements Document](docs/PRD.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
