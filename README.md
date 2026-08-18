# Business Internship Aggregator

## Overview

Business Internship Aggregator is an in-progress platform that automatically discovers and aggregates business-related internship opportunities from company career websites, presenting them in one searchable interface. It is being built as both a portfolio project and a genuinely useful tool for business students.

## Problem

Business students looking for internships in Product Management, Business Analytics, Finance, Accounting, Consulting, Marketing, Operations, Supply Chain, Strategy, or Human Resources have to manually check dozens of individual company career pages, since opportunities are scattered with no central source. Most existing internship aggregators are built for and optimized around software engineering roles, leaving business students underserved.

## Solution

An automated pipeline that scrapes company career pages for business-relevant internships, normalizes and deduplicates the data, stores it in a central database, and exposes it through a searchable, filterable web interface — kept up to date without requiring students to check each company site individually.

## Current Status

**Full stack MVP working end-to-end (Phases 1–4 complete).** PostgreSQL schema, SQLAlchemy models, and Alembic migrations are implemented and tested. Scrapers are implemented for three real companies (Robinhood, Cloudflare, Braze — all Greenhouse-hosted) behind a shared, tested `BaseScraper`/`GreenhouseScraper` architecture, with 9 real internship records currently stored. A read-only FastAPI backend (search, filtering, pagination, sorting) is implemented and tested against that live data. A Next.js (App Router, TypeScript, Tailwind) frontend consumes that API — search, filters, sorting, pagination, internship and company detail pages — tested against the live backend. See `docs/roadmap.md` for the full phase-by-phase build order.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Scraping | Python, Playwright |
| Automation | GitHub Actions |
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

## Running Locally

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
│   ├── companies/      # Company-specific scraper configs (Robinhood, Cloudflare, Braze)
│   ├── base_scraper.py     # Shared DB/lifecycle logic for all scrapers
│   ├── greenhouse.py       # Shared Greenhouse ATS fetch/parse logic
│   ├── classification.py   # Title -> category classification
│   └── scheduler.py        # Not yet built (Phase 6)
├── database/           # database/schema.sql (source-of-truth DDL)
├── alembic/             # Migrations
├── docs/                # Product and technical documentation
└── README.md
```

## Documentation

- [Product Requirements Document](docs/PRD.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
