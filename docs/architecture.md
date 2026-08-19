# Architecture Overview

This document describes the technical architecture for the MVP. As of Phase 6, the full stack is implemented, tested, and deployed to production (see "Production Architecture" below and `roadmap.md` for phase-by-phase build order).

## High-Level Flow

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

## Component Responsibilities

### Frontend (Next.js + React + Tailwind CSS)

Responsible for presenting internship data to the user and translating user interaction into API calls. Specifically:
- Rendering a searchable, filterable list of internships.
- Rendering an internship detail view.
- Sending search/filter parameters to the FastAPI backend and rendering results.
- Linking out to the original company application page for each listing.

The frontend holds no business logic beyond presentation and query construction — all filtering/search logic lives in the backend/database layer.

### Backend (FastAPI)

Responsible for exposing internship data to the frontend (and any future clients) over a REST API. Specifically:
- Querying PostgreSQL for internship records.
- Implementing search (keyword) and filter (category, company, location) query parameters.
- Implementing pagination for list endpoints.
- Validating request parameters and returning consistent JSON responses.

The backend does not scrape data itself — it only reads from (and, internally, writes to) the database that scrapers populate.

### Database (PostgreSQL)

Responsible for durable storage of normalized internship data. Stores:
- Internship postings (title, company, category/function, location, description, application URL, source, date first detected, date last seen, active/inactive status).
- Company metadata (name, career page URL, associated scraper identifier).
- Fields needed to support duplicate detection (e.g., a normalized/hashed representation of title+company+location, or the source URL as a natural key).

PostgreSQL is the single source of truth. Both the scraping pipeline and the API read/write against it — there is no separate cache or search index in the MVP.

### Scrapers (`scrapers/companies/`)

Each company gets its own scraper module responsible for:
- Navigating that company's specific career site structure using Playwright.
- Extracting raw posting data (title, location, description, link, etc.) relevant to business roles.
- Handing raw extracted data off to the normalization step — scrapers should not normalize or deduplicate themselves.

Company scrapers are intentionally isolated from one another so that one company's site changing/breaking doesn't affect others.

### `base_scraper.py`

Defines a shared scraper interface/base class that all company-specific scrapers inherit from, so scrapers are consistent and swappable. Conceptually, it should define:
- A common lifecycle (e.g., `setup` → `fetch_listings` → `parse_listing` → `teardown`).
- A standard return format that every scraper must produce, regardless of the source site's structure, so downstream normalization can treat all scrapers identically.
- Shared error handling/logging so an individual scraper's failure is caught and reported instead of crashing the run.

Company scrapers implement the site-specific parsing logic; `base_scraper.py` enforces the contract they must follow.

### Scheduler (`scheduler.py`)

Responsible for triggering scraping jobs on a recurring basis. Conceptually, it will:
- Maintain (or read from config/DB) the list of company scrapers to run.
- Invoke each company scraper in turn (or in parallel, within reasonable limits), independently of the others.
- Hand successfully scraped/normalized data off to the duplicate detection and storage step.
- Log per-scraper success/failure for observability.

In the MVP, the scheduler is invoked manually or via a GitHub Actions workflow on a schedule (see Automation phase in `roadmap.md`) — no long-running process or external job queue is required.

## Data Flow: From Company Website to User

1. A scheduled (or manually triggered) run starts the scheduler.
2. The scheduler invokes each company-specific scraper (built on `base_scraper.py`).
3. Each scraper uses Playwright to load the company's career page and extract raw internship listings relevant to business roles.
4. Raw listings are passed through a normalization step, converting them into a consistent internal schema (title, company, category, location, description, URL, dates).
5. Normalized listings pass through duplicate detection, which checks them against existing records (e.g., by source URL or a normalized title+company+location signature) before insert/update.
6. New or updated listings are written to PostgreSQL; existing unchanged listings are left as-is (or have their "last seen" timestamp updated).
7. FastAPI reads from PostgreSQL to serve search/filter/list requests from the frontend.
8. The Next.js frontend calls the FastAPI backend and renders results for the user, who can search, filter, and click through to the original application page.

## Out of Scope for This Architecture (For Now)

- No microservices — the backend is a single FastAPI application.
- No Kubernetes or container orchestration.
- No Databricks or big-data infrastructure.
- No search index (e.g., Elasticsearch) — PostgreSQL query capabilities are sufficient at MVP scale.
- No AI/ML components.

## Implementation Notes (Phase 1 — Database)

The concrete schema is defined in [`database/schema.sql`](../database/schema.sql) and mirrored by SQLAlchemy models in `backend/models/`. Two tables: `companies` and `internships`, with a one-to-many relationship (a company has many internships; `internships.company_id` uses `ON DELETE RESTRICT` so a company can't be hard-deleted while historical internship data still references it — use `companies.is_active` instead).

Duplicate internships are prevented via a `dedupe_key` column — a hash of `company_id + normalized(title) + normalized(location)` computed in `backend/database/utils.py`, not a raw URL (career-site URLs often carry session/tracking parameters that vary between scrapes of the same posting). Full reasoning is documented alongside the schema in `schema.sql`.

Database access uses synchronous SQLAlchemy (`backend/database/session.py`) and Alembic for migrations (`alembic/`), both configured via the `DATABASE_URL` environment variable — never hardcoded credentials.

## Implementation Notes (Phase 2 — Scraping MVP)

`scrapers/base_scraper.py` defines `BaseScraper`, an abstract class shared by every company scraper. A subclass implements only two methods — `fetch_raw_listings()` (however the site needs to be reached) and `parse_listing(raw)` (turn one raw item into a `NormalizedInternship`, defined in `scrapers/schemas.py`, or return `None` to filter it out). `BaseScraper.run()` handles everything else identically across companies: looking up or creating the `Company` row, computing each listing's `dedupe_key` via the existing `compute_dedupe_key()`, inserting new internships or updating existing ones (bumping `last_seen_at`/`is_active`), isolating per-listing parse errors so one bad record can't crash a run, and logging a summary.

`fetch_raw_listings()` is deliberately not tied to Playwright — a subclass uses whichever transport fits the target site. A future company without a public API (e.g. many Workday-hosted career sites) would implement `fetch_raw_listings()` with Playwright instead, in the same slot, without touching `BaseScraper`.

## Implementation Notes (Phase 2B — Multi-Company Validation)

Adding a second and third company (Cloudflare, Braze) confirmed that Greenhouse's raw JSON schema (title, location, offices, departments, absolute_url, content, first_published, application_deadline) is identical across companies, so `scrapers/greenhouse.py` now provides a shared `GreenhouseScraper(BaseScraper)` that implements `fetch_raw_listings()` and `parse_listing()` once. Individual company files (`scrapers/companies/robinhood.py`, `cloudflare.py`, `braze.py`) are now just config — `board_token`, `company_slug`, `company_name`, `career_url`, `website_url` — with no fetch/parse logic of their own. This wasn't abstraction for its own sake: it replaced what would otherwise have been three near-identical copies of the same fetch/parse code, and it directly fixed a real bug (see below). A hypothetical future ATS without a public API (e.g. Workday) would get its own `WorkdayScraper(BaseScraper)` sibling, not a subclass of `GreenhouseScraper`.

Title-to-category classification was factored out into `scrapers/classification.py` (`classify_internship()`), shared by `GreenhouseScraper` and reusable by any future ATS-specific scraper, since classification is about job-title semantics, not how the data was fetched. Testing against real data from three companies drove two concrete fixes:
- **Specific phrases now outrank generic ones.** Robinhood's "Market Research Strategy Intern" was landing in *Strategy* rather than *Business Analytics*, purely because "strategy" appeared earlier in the keyword list than "market research". Category matching now picks the *longest* matching keyword phrase, not the first one in list order.
- **A missed exclusion.** Cloudflare's "Research Engineer Intern" postings weren't caught by the existing technical-role exclude list (which had "software engineer" etc. but not "research engineer") and would have been miscategorized as a business internship. Added.

Two findings were deliberately *not* papered over:
- Cloudflare's "GRC Team Intern" (governance/risk/compliance) doesn't fit any of the platform's 11 fixed categories and correctly falls back to `Other` rather than being force-matched to something misleading.
- Braze's "Business Development Representative Intern" is a sales/BD role with no matching category (`Other` again) — a real gap in the category taxonomy, not a bug. Worth considering a `Sales`/`Business Development` category in a future phase; not added here since it would require changing the `internship_category` Postgres enum, out of scope for this validation pass.

Also fixed: Cloudflare's `location.name` field is a generic placeholder ("In-Office") rather than a real place, while `offices[0].name` reliably holds the actual city. `GreenhouseScraper` now prefers `offices` when present. This wasn't cosmetic — two Cloudflare "Network Strategy Intern" postings share an identical title but have different real offices (London vs. Austin, TX); without this fix both would have normalized to the same location and collapsed into a single `dedupe_key`, silently dropping one of two genuinely distinct open roles.

## Implementation Notes (Phase 3 — FastAPI Backend)

```text
Scrapers  →  PostgreSQL  →  FastAPI  →  Next.js Frontend
```

The API layer (`backend/api/`) is a thin, read-only presentation layer over the database — it owns no business logic that the scrapers or database don't already own. Its responsibilities are: translate HTTP query parameters into validated SQLAlchemy queries, shape ORM objects into public response schemas (so internal-only fields like `dedupe_key` are never exposed), and return clean HTTP semantics (404s, 422s) instead of leaking database internals.

- `backend/api/main.py` — the FastAPI app: CORS (origin list from `CORS_ALLOWED_ORIGINS`), a global handler that turns any `SQLAlchemyError` into a generic 500 (never exposing SQL or connection details), and router registration.
- `backend/api/dependencies.py` — `get_db()`, a request-scoped SQLAlchemy session (reuses the existing `backend/database/session.py` engine; no second database connection system).
- `backend/api/schemas/` — Pydantic response models (`InternshipOut`, `CompanyOut`, etc.), built with `from_attributes=True` so they validate directly off ORM objects. Categories are never redefined here — `GET /categories` reads `InternshipCategory` directly from `backend/models/internship.py`.
- `backend/api/routes/` — `internships.py` (list with search/filter/sort/pagination, detail), `companies.py` (list with an active-internship count via a correlated subquery, detail with its active internships), `categories.py`.

Every internship list/detail query does a single `JOIN` to `companies` with `contains_eager()` to load the company alongside each internship in one query, avoiding an N+1 query per internship. The company list's `active_internship_count` uses a correlated scalar subquery for the same reason — one query total, not one count query per company.

Search (`?search=`) and the `location=`/`company=` filters use PostgreSQL `ILIKE` for case-insensitive partial matching — no Elasticsearch, no raw SQL string interpolation (all values are bound parameters via SQLAlchemy's query builder). `category` and `sort` are validated against fixed enums by FastAPI/Pydantic, so an invalid value returns a 422 with the list of accepted values rather than silently returning nothing.

## Implementation Notes (Phase 4 — Next.js Frontend)

```text
Career Sites → Scrapers → PostgreSQL → FastAPI → Next.js → User
```

The frontend (`frontend/`, Next.js App Router + TypeScript + Tailwind) is a thin presentation layer: it owns no filtering/search/sort logic of its own — every one of those operations is a query parameter sent to the existing FastAPI endpoints, never client-side data manipulation.

**Server-first architecture.** The home page (`app/(home)/page.tsx`) and both detail pages (`app/internships/[id]/page.tsx`, `app/companies/[id]/page.tsx`) are async Server Components that read the URL (search params or route params), call the typed API client (`frontend/lib/api.ts`), and render server-side — there is no client-side data fetching, loading spinners driven by `useEffect`, or duplicate requests. The URL is the single source of truth for search/filter/sort/page state (Step 12): interactive controls (`SearchBar`, `FilterPanel`, `SortSelect` — the only Client Components, marked `"use client"`) don't hold their own request state, they just read the current URL via `useSearchParams()`, merge in a change, and `router.push()` a new URL, which re-renders the server page. `Pagination` needs no client JS at all — it's a Server Component rendering plain `<Link>`s with hrefs computed from the current query params.

`frontend/lib/api.ts` centralizes every backend call (`getInternships`, `getInternship`, `getCompanies`, `getCompany`, `getCategories`) behind a typed client that builds query strings via `URLSearchParams` (never raw string concatenation) and always fetches with `cache: "no-store"`, since internship data changes as scrapers run. `frontend/lib/types.ts` mirrors the Pydantic response schemas by hand (no codegen — small enough surface area that keeping them manually in sync is simpler than adding a generator dependency).

**Loading and error states use Next.js's own file conventions** rather than manual state management: a route-level `loading.tsx` is shown automatically while a Server Component awaits data, and `error.tsx` is a React error boundary that catches thrown fetch failures and offers a "Try again" button (via the `reset()` callback Next.js provides). `notFound()` (from `next/navigation`) triggers `not-found.tsx` for a missing internship or company ID.

One consequence of this required a deliberate fix: a `loading.tsx` file makes Next.js wrap that route in a `<Suspense>` boundary, and per Next.js's own documentation, once a Suspense-wrapped response starts streaming as `200 OK`, calling `notFound()` deeper in the tree can no longer change the HTTP status code (it's already been sent) — the not-found *content* still renders correctly, but the status stays `200`. This was caught by testing (`curl` showed `200` for `/internships/999999`), not assumed away. The fix: only the home page needs a loading skeleton, so `loading.tsx` was scoped to a `(home)` route group containing just the home page. The two detail pages have no `loading.tsx` ancestor, so they render as fully blocking dynamic routes and return correct status codes — verified via `curl`: `404` for a missing internship/company ID, `500` (via `error.tsx`) when the backend is unreachable.

**Verified via `curl` against the live backend** (no browser available in this environment): status codes for all routes (200/404/500), search/category/company/location filters and their combination, sorting, pagination links, URL-param round-tripping (search input `value` reflects `?search=`), the Apply button's `href` matching the internship's real `application_url`, and empty/error state content. **Not verifiable without a browser**, and therefore not claimed as tested: actual visual responsive layout on mobile/tablet, click/keyboard interaction, focus-visible styling, and the exact client-side transition/pending-state behavior (`useTransition`) — these follow standard, deliberately-chosen Tailwind responsive utilities and accessibility patterns (semantic HTML, `<label>`s, `sr-only` text, `aria-current`/`aria-disabled` on pagination) but are unverified beyond code review and a successful production build (`npm run build`, zero TypeScript errors).

## Production Architecture (Phase 6 — Deployment)

```text
Company Career Websites
        ↓
     Scrapers (scrapers/scheduler.py)
        ↓
   GitHub Actions (scheduled every 6h + workflow_dispatch)
        ↓
  Managed PostgreSQL (Neon)
        ↑ (also read by)
     FastAPI (Render)
        ↓
     Next.js (Vercel)
        ↓
       User
```

**Frontend hosting (Vercel).** `frontend/` deploys automatically on push to `main`. Vercel's Root Directory is set to `frontend` so the Next.js app builds independently of the Python backend in the same repo. `NEXT_PUBLIC_API_BASE_URL` is a Vercel project environment variable pointing at the Render API URL — never hardcoded, per the existing `frontend/lib/api.ts` pattern of reading it from `process.env`.

**Backend hosting (Render).** A single free Web Service, deployed via the `render.yaml` Blueprint at the repo root (infrastructure-as-code, so the service configuration itself is versioned). Build command installs `requirements.txt`; start command runs `alembic upgrade head && uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT` — migrations apply automatically on every deploy (idempotent, so this is safe to run repeatedly), and there is no `--reload` or debug flag. Render's own health check hits `GET /`. `DATABASE_URL` and `CORS_ALLOWED_ORIGINS` are Render environment variables (`sync: false` in `render.yaml`, meaning Render prompts for them in its dashboard rather than storing values in the repo).

**Database hosting (Neon).** Managed serverless Postgres, free tier. The production schema was created exclusively through `alembic upgrade head` run against the Neon connection string — no manual DDL — and verified to match the local schema exactly (tables, indexes, the `internship_category` enum, and the `internships.company_id` `ON DELETE RESTRICT` foreign key). Neon's pooled connection string (the `-pooler` host) is used since both Render and GitHub Actions connect intermittently rather than holding a persistent connection pool of their own.

**GitHub Actions (`.github/workflows/scraper.yml`).** Runs on a `0 */6 * * *` cron (every 6 hours, UTC) and via manual `workflow_dispatch`. Steps: checkout → Python 3.12 → `pip install -r requirements.txt` → `alembic upgrade head` → `python -m scrapers.scheduler`. A `concurrency` group prevents overlapping runs (a manual trigger racing a scheduled one) from writing to the database at the same time. `DATABASE_URL` is a GitHub Actions repository secret, referenced via `${{ secrets.DATABASE_URL }}` and never printed to logs.

**Scraper execution.** `scrapers/scheduler.py` is the entry point both locally and in CI: it iterates a fixed list of company scraper classes (`RobinhoodScraper`, `CloudflareScraper`, `BrazeScraper`), running each independently. One company's scraper raising an exception outright (e.g. its API is unreachable) is caught, logged, and skipped — it does not stop the other companies' scrapers, and because each `BaseScraper.run()` commits its own transaction, a failed company never leaves partial writes. Within a single company's run, `BaseScraper.run()` now also reconciles lifecycle state: any internship still marked active in the database but absent from that run's fetched listings is set `is_active = False` (added in Phase 6 — previously nothing did this). This only runs after a successful fetch, so a scraper that fails before returning any listings can never mass-deactivate a company's postings.

**Environment variables and environment separation.** Local development reads `.env` (backend, via `python-dotenv`) and `frontend/.env.local` (frontend), both gitignored. Production configuration is split across three separate surfaces that all happen to reference the same values: Render environment variables (used by the live API process), Vercel environment variables (used at frontend build/runtime), and GitHub Actions repository secrets (used by the scheduled scraper job). No production credential is ever committed, logged, or printed — verified against the full git history, not just the current `.gitignore`.

**Production vs development.** The only difference in application code between environments is which values the existing env-var reads (`DATABASE_URL`, `CORS_ALLOWED_ORIGINS`, `NEXT_PUBLIC_API_BASE_URL`) resolve to — there is no separate "production mode" branch of logic, no feature flags, and no hardcoded environment-specific URLs anywhere in the codebase.
