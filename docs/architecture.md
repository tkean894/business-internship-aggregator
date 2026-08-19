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

**Scraper execution.** `scrapers/scheduler.py` is the entry point both locally and in CI: it iterates a fixed list of company scraper classes (8 as of Phase 7 - see "Scraper Architecture" below), running each independently. One company's scraper raising an exception outright (e.g. its API is unreachable) is caught, logged, and skipped — it does not stop the other companies' scrapers, and because each `BaseScraper.run()` commits its own transaction, a failed company never leaves partial writes. Within a single company's run, `BaseScraper.run()` now also reconciles lifecycle state: any internship still marked active in the database but absent from that run's fetched listings is set `is_active = False` (added in Phase 6 — previously nothing did this). This only runs after a successful fetch, so a scraper that fails before returning any listings can never mass-deactivate a company's postings.

**Environment variables and environment separation.** Local development reads `.env` (backend, via `python-dotenv`) and `frontend/.env.local` (frontend), both gitignored. Production configuration is split across three separate surfaces that all happen to reference the same values: Render environment variables (used by the live API process), Vercel environment variables (used at frontend build/runtime), and GitHub Actions repository secrets (used by the scheduled scraper job). No production credential is ever committed, logged, or printed — verified against the full git history, not just the current `.gitignore`.

**Production vs development.** The only difference in application code between environments is which values the existing env-var reads (`DATABASE_URL`, `CORS_ALLOWED_ORIGINS`, `NEXT_PUBLIC_API_BASE_URL`) resolve to — there is no separate "production mode" branch of logic, no feature flags, and no hardcoded environment-specific URLs anywhere in the codebase.

## Implementation Notes (Phase 7 — Scraper Expansion & Data Quality)

Goal: prove the scraper architecture generalizes beyond three same-ATS companies, and tighten data quality now that there's enough real, varied data to find its actual weak points.

### Scraper Architecture

```text
BaseScraper
├── GreenhouseScraper
│   ├── Robinhood, Cloudflare, Braze (Phase 2/2B/5)
│   └── Rocket Lab, SpaceX, Red Ventures, SpotHopper (Phase 7)
└── WorkdayScraper
    └── Abbott Laboratories (Phase 7)
```

**WorkdayScraper (`scrapers/workday.py`)** is the platform's first non-Greenhouse ATS integration. Like Greenhouse, Workday's own career-site frontend calls a public, unauthenticated JSON API (`/wday/cxs/{tenant}/{site}/jobs`) - no authentication, CAPTCHA, or anti-bot measure is bypassed; confirmed against each tenant's own `robots.txt` (Abbott's explicitly `Allow: /abbottcareers/`, disallowing only `/nonpublic/` and `/refreshFacet/`). The practical difference from Greenhouse is volume: Greenhouse returns an entire company's board in one request, while Workday paginates at a hard-capped 20 results per page and only returns a title/location summary per job, requiring a second per-job request for the full description. To keep request volume proportionate (a large global employer like Abbott has ~2,000 open roles total), `WorkdayScraper` narrows the query server-side to Workday's own `workerSubType` facet for "Intern/Student" postings - a GUID specific to each tenant, found once via that tenant's own facet listing and set as `intern_facet_id` in the company config - and further pre-filters by title (`INTERN_TITLE_RE`) before paying for the second request. This cut Abbott's per-run request count from thousands to about 40. A company config only sets `base_url`/`tenant`/`site`/`intern_facet_id` plus the usual `BaseScraper` fields; all fetch/pagination/parsing logic is shared, mirroring how `GreenhouseScraper` factors out its ATS-specific equivalent.

**Shared utilities (`scrapers/http_utils.py`, `scrapers/text_utils.py`).** Both ATS scrapers now share one retry/backoff-configured `requests.Session` (3 retries, exponential backoff, retrying only transient failures - connection errors, timeouts, HTTP 429, and temporary 5xx - never a permanent 404) and one set of HTML-description-cleaning / date-parsing / location-normalization helpers, rather than each ATS module reimplementing them.

### Classification Quality

Company expansion immediately surfaced two real, previously-latent bugs in `scrapers/classification.py`, both fixed and covered by regression tests in `tests/test_classification.py`:

1. **Substring false positives.** The original keyword matching was a plain `keyword in title.lower()` substring check. Adding a `Sales` category with the keyword `"sales"` would have miscategorized a hypothetical "Salesforce Administrator Intern" as Sales, since "sales" is a literal substring of "Salesforce". Matching was rewritten to compiled word-boundary regexes (`_keyword_pattern`) - a leading `\b` on every keyword, computed once per keyword at module load rather than per title. A small, explicit exception (`_PREFIX_MATCH_PHRASES`) drops the *trailing* boundary only for the two phrases that must also match as a prefix of a longer word ("engineering intern" needs to match "...Engineering **Internship**" too).
2. **Technical roles leaking into OTHER.** The original `EXCLUDE_KEYWORDS` list only covered software-engineering terms, so aerospace-hardware internships from Rocket Lab and SpaceX (Avionics, Manufacturing Engineering, Flight Software, Civil/Silicon Engineering, etc.) were falling into `OTHER` as if they were unclassified *business* roles - misleading, since `OTHER` is meant to mean "a real business function without a fixed category," not "a technical role that slipped past the filter." `EXCLUDE_KEYWORDS` gained several targeted additions, each tied to a real observed title (see comments in `classification.py`).

**New category: Sales.** Braze's "Business Development Representative Intern" (Phase 5), Abbott's "Commercial Excellence Intern", and SpotHopper's "Business Development Internship" (Phase 7) are real, recurring postings across three companies with no existing category to land in - a legitimate taxonomy gap per the project's own stated principle ("do not force jobs into incorrect categories simply to avoid Other"), not a one-off. Added end-to-end: Postgres enum (`ALTER TYPE internship_category ADD VALUE 'Sales'`), SQLAlchemy enum, `scrapers/classification.py` keywords, `frontend/lib/types.ts`. No backend API or frontend filter-component code needed to change - both already read the category list dynamically (`GET /categories` reads the enum directly; `FilterPanel` renders whatever that endpoint returns).

**HR keyword gap.** Rocket Lab's "Learning & Development Intern" is a real, standard HR sub-function with no existing synonym in the `HUMAN_RESOURCES` keyword list; added `"learning & development"` / `"learning and development"`.

### Data Quality Validation

`scrapers/schemas.py` now has `validate_normalized_internship()`, called in `BaseScraper.run()` after `parse_listing()` succeeds and before the listing is upserted. It checks: non-empty title (and within the `VARCHAR(500)` column limit), `application_url`/`source_url` are absolute HTTP(S) URLs, and `application_deadline` isn't before `posted_date`. A listing that fails validation is logged with the specific reason and skipped (counted in `error_count`), never silently dropped and never crashing the run - the same isolation pattern already used for per-listing parse errors. Category validity is already guaranteed by the type system (`NormalizedInternship.category: InternshipCategory` - an invalid value fails at construction, inside the existing per-listing `try/except`), so it isn't re-checked here. Location normalization (whitespace collapsing) and description cleaning (HTML-to-text) happen earlier, in the shared `text_utils` helpers every ATS scraper's `parse_listing()` calls.

### A Real Dedup Collision, Found by Testing

`database/schema.sql`'s "Deduplication Strategy" section always documented a known limitation: `dedupe_key = hash(company_id + normalized(title) + normalized(location))` cannot distinguish two genuinely different postings that happen to share an identical title and location. This had never actually been hit until Rocket Lab was added: it runs two distinct open reqs both titled "Business Analyst Intern - Supply Chain" at the same "Auckland Production Complex Office" location. The first local test run crashed the entire company's scraper run on a Postgres unique-constraint violation (both rows landed in the same `INSERT` batch). Rather than redesigning the dedupe strategy (out of scope - the existing key intentionally avoids raw URLs, since ATS URLs carry tracking/session parameters that vary between scrapes of the same real posting), `BaseScraper.run()` now detects a same-run key collision before attempting the insert, logs it clearly (surfaced in both `ScraperRunResult.errors` and the persisted `scraper_runs.error_count`), and skips the second listing - so one of the two real postings is known to be represented, not silently lost, and the run completes instead of crashing. This is a direct, honest consequence of the documented dedup tradeoff, not a new bug.

### Scraper Run Metrics

A new `scraper_runs` table (`backend/models/scraper_run.py`, migration `dfdc769405fd`) persists one row per company-scraper invocation: `company_slug`, `scraper_name`, `started_at`/`completed_at`, `status` (`success`/`failed`), and the same counts already tracked in-memory by `ScraperRunResult` (`raw_count`, `relevant_count`, `created_count`, `updated_count`, `deactivated_count`, `skipped_count`, `error_count`), plus a truncated `error_message` on failure. `BaseScraper._record_run()` writes this row in a dedicated short-lived session, independent of the main working session, so a run's outcome is recorded even when that session was never opened (a fetch-level failure) or already closed - deliberately not sharing the working session, so a metrics-write is never coupled to the success/failure of the actual scrape it's describing. Not exposed through the public API (Phase 7 Step 18 - internal operational data only); query it directly against the database for now.

### Error Handling

`BaseScraper.run()` distinguishes three failure classes, all logged with company/scraper/error-type context and never including secrets: (1) a fetch-level failure (network/HTTP, after `http_utils`' retry policy is exhausted) - the whole company run fails, nothing has been written yet; (2) a database-processing failure (e.g. a constraint violation) - also a hard failure, logged separately since the fetch itself succeeded; (3) a per-listing parse or validation failure - isolated, logged, counted, and skipped without affecting the rest of that company's run. All three record a `scraper_runs` row.

## Implementation Notes (Phase 8 — Dataset Expansion & Product Polish)

Goal: prove the platform's usefulness scales past a thin, tech/aerospace-skewed dataset, and make the frontend feel like an actual discovery product rather than a raw search form.

### ATS Architecture: Lever

```text
BaseScraper
├── GreenhouseScraper  (7 companies)
├── WorkdayScraper     (8 companies)
└── LeverScraper       (HCVT)
```

`LeverScraper` (`scrapers/lever.py`) is the platform's third ATS, added only after confirming a real, verified need: HCVT (a tax/accounting/advisory firm) had 12 clean, currently-open Accounting/Consulting internships across distinct offices, with no dedup-collision risk. It uses Lever's own officially documented, unauthenticated Postings API (`api.lever.co/v0/postings/{site}` - see `github.com/lever/postings-api`, maintained by Lever), explicitly designed for public career-site/job-board consumption - architecturally the simplest of the three ATSs, since one request returns a company's entire posting list already (like Greenhouse, unlike Workday's per-job detail requests). A specific access question came up during evaluation and is worth recording: `jobs.lever.co` (Lever's separate hosted-posting-page domain) has a robots.txt rule disallowing `ClaudeBot` specifically, distinct from its generic `Allow: /` for other bots; `api.lever.co` (the only host this scraper ever talks to) carries no such restriction. The distinction was treated as meaningful rather than a loophole - confirmed the Postings API is Lever's own sanctioned public interface (not reverse-engineered), and the scraper never touches `jobs.lever.co` or Lever's separate authenticated OAuth Data API.

### Company Industry Metadata

`Company.industry` (nullable `VARCHAR(100)`, migration `dda83df7adaa`) is free text, not a fixed enum - unlike `internship_category`, the set of industries is expected to grow organically as companies are added, and a rigid taxonomy would need its own migration every time a new industry showed up. Each company config sets `industry` as a class attribute (e.g. `industry = "Healthcare"`); `BaseScraper._get_or_create_company()` sets it on creation and refreshes it on every subsequent run if the config value changes, so the 8 companies that predated this field were backfilled automatically on their next scheduled run rather than needing a one-off data migration script. Exposed via `GET /internships?industry=` (exact match, joined through `Company`) and surfaced in `CompanySummary`/`CompanyOut` - no new endpoint was added; the frontend derives its industry filter options from the existing `GET /companies` response.

### Classification: Real Estate Category and Further Refinements

All changes here were driven by titles actually observed from the 8 new companies, following the same evidence-based bar as Phase 7:

- **New `Real Estate` category** - Invesco's recurring "Early Career Intern - Real Estate (Equity & Credit)" postings, explicitly suggested as a candidate category in this phase's own task definition and backed by real, repeated volume.
- **Finance keywords**: `investment(s)`, `risk`, `actuarial`, `equity`/`equities` - Invesco (investment management) and AIA (insurance/actuarial) postings that don't fit any other category cleanly enough to justify their own new category yet (too little distinct volume, per the "only add a category if there are enough real postings" rule applied in Phase 7).
- **Accounting keyword**: `tax` - HCVT's Tax/International Tax/State and Local Tax internships.
- **A real regex bug, found by testing**: Medtronic's "Cardiovascular _Marketing Intern" (a stray underscore from a messy ATS export) did not match `\bmarketing\b`, because regex word-boundaries treat `_` as a word character - the character immediately before "marketing" was never a boundary. Fixed by normalizing separator punctuation (`_`, `/`) to spaces before matching (`_normalize_for_matching` in `classification.py`), rather than special-casing this one title.
- **Broadened technical exclusions** per this phase's explicit list: `mechanical engineer`, `electrical engineer`, `computer engineer`, `embedded engineer`/`embedded systems`, `cyber security`, `it intern`.
- **The Phase 7 dedup-collision handling was exercised for real, repeatedly**: AIA and Medtronic both post multiple identical-title-and-location openings (e.g. AIA's "Intern, Testing" appears 4 times at the same Kuala Lumpur office). Each collision was skipped and logged exactly as designed - confirmed this generalizes beyond the single Rocket Lab case that originally motivated it, not a new bug.
- **`Other` is 48/118 active internships (~41%) in production as of this phase** - slightly higher than Phase 7's 34%, not lower, despite the additions above. This is disclosed rather than smoothed over: AIA and Medtronic between them contribute a large volume of generically- or internally-titled international postings (e.g. "Agency, Intern", "Intern, Process Transformation", "NMPH Operation Intern") that are genuinely ambiguous - forcing them into a specific category to shrink the `Other` percentage would violate the platform's own stated principle against forced classification.

### Freshness

Two different timestamps answer two different questions, and the platform is deliberately careful never to conflate them (Phase 8 Step 9's core requirement): `Internship.posted_date` is the source's own claim about when the role went live (not every ATS provides one - Workday's job detail response omits an application deadline entirely, for instance, and some sources' dates are approximate); `Internship.first_seen_at` is strictly this aggregator's own observation - when a scraper run first inserted the row, never adjustable by source data. `frontend/lib/format.ts`'s `freshnessLabel()` shows "Posted X ago" when a real `posted_date` exists, and falls back to "Discovered X ago" (from `first_seen_at`) only when it doesn't - the copy itself signals which kind of date is being shown, so a listing missing a source date is never presented as if the platform knew when it was actually posted. The "New" badge (`isNewlyDiscovered()`) is intentionally always based on `first_seen_at` (≤ 7 days), not `posted_date`, since discovery time is the one signal every listing always has regardless of source data quality.

### Frontend / Product

All additions reuse the existing `frontend/lib/api.ts` client and existing endpoints - no new client-side data-fetching pattern, no new Client Components beyond extending the two that already existed (`FilterPanel`, `SortSelect`). The homepage's live stats line is derived from data already fetched for the filter panel (summing `active_internship_count` across `GET /companies`' response, and `categories.length` from the existing `GET /categories` call) rather than issuing an extra request. Category-pill and company-list "discovery" (`/companies`, a new Server Component page) both link back into the existing `?category=`/detail-page query-param filtering rather than introducing parallel pages or endpoints. (A "Recently Added" section was briefly added and then removed after shipping - see the git history around the homepage pagination fix - once it became clear the USA-location display filter needed pagination to run over the fully-filtered result set rather than a single fetched page.)

**Responsive design and accessibility**: reviewed via the rendered HTML and Tailwind utility classes actually present (no obvious layout overflow, `flex-wrap` used throughout the filter/pill rows, existing `sm:`/mobile-first breakpoints extended consistently to new elements) and via `sr-only` labels on every new form control (the industry `<select>` follows the exact pattern of the existing category/company selects). No visual browser-based testing was performed or claimed - this environment has no browser - consistent with how Phase 4's original frontend work was verified (`curl` against real rendered output only).

## Implementation Notes (Phase 8 — Accounts, Saved Internships & Notifications)

Goal: let users create accounts, save internships, and get emailed about new matches or saved internships going inactive - without weakening anonymous browsing, without a second scheduler, and without the frontend's own claims about who's signed in ever being trusted by the backend.

### Authentication

Chosen: **Clerk**. The frontend and backend are two independently-deployed services (Next.js on Vercel, FastAPI on Render) - whatever "signed in" means has to be verifiable by FastAPI on its own, not just asserted by whatever the browser sends. Clerk issues a signed JWT per session; `backend/api/auth.py` verifies it independently using `PyJWT`'s `PyJWKClient` against Clerk's own public JWKS endpoint (`CLERK_JWKS_URL`) - no shared secret, no trusting the frontend, and a forged token (even one that reuses Clerk's real, publicly-visible key ID) fails signature verification (see `tests/test_auth.py`, which tests this against Clerk's real JWKS, not a mock). `get_current_user_optional()` returns `None` for a request with no `Authorization` header at all (the normal anonymous case - never an error) but rejects a *present but invalid/expired* token with 401, so a client can always distinguish "not signed in" from "your session expired."

`backend/models/user.py`'s `User` table deliberately never stores a password or session token - only `clerk_user_id` (Clerk's own identifier) and a cached `email` (looked up once, on first sign-in, via Clerk's Backend API - `backend/services/clerk_client.py` - so composing a notification email never needs a live Clerk API call). Clerk remains the sole source of truth for credentials.

The Next.js app needs `CLERK_SECRET_KEY` too, separately from the backend's copy - a real, non-obvious finding from actually deploying this: `@clerk/nextjs`'s own middleware (`frontend/middleware.ts`) and `auth()` server helper verify sessions server-side using that key, which is a completely different use from the backend's (which only calls Clerk's Backend API for the one-time email lookup above). Both are legitimate; neither exposes the secret to the browser.

### Database

Four new tables (migration `ae99487d261d`), all via Alembic, none touching existing tables' data:

- **`users`** — see above.
- **`saved_internships`** — `UNIQUE(user_id, internship_id)` is the actual mechanism preventing a duplicate save, enforced by Postgres, not application logic; both foreign keys are `ondelete="CASCADE"`. Deliberately does not mirror the internship's `is_active` state - a saved internship going inactive is discovered by joining through to the live `Internship` row (see "Saved Internship Lifecycle" below), so it can never drift out of sync with the real scraper-maintained state.
- **`notification_preferences`** — one row per user; `categories`/`industries`/`locations` are plain Postgres `TEXT[]` arrays (not a DB enum, unlike `internship_category`) validated against `InternshipCategory` at the Pydantic layer instead - an empty array means "no filter on this dimension," not "matches nothing." `last_notified_at` is only ever touched for daily/weekly (digest) frequencies; an immediate-frequency user's cadence is always "now."
- **`notification_events`** — see "Notification idempotency" below; this table *is* the idempotency mechanism, not just a log of one.

### Saved Internships

`POST /internships/{id}/save` and `DELETE /internships/{id}/save` (both requiring auth via `get_current_user`) live in `backend/api/routes/internships.py` alongside the existing read endpoints, reusing the same `Internship`/`Company` models. Saving uses `INSERT ... ON CONFLICT DO NOTHING` against the unique constraint rather than a check-then-insert, so a duplicate save is a safe no-op even under concurrent requests (a check-then-insert has a race window; the database constraint does not). Unsaving a never-saved internship is a no-op 204, not an error. `GET /internships` and `GET /internships/{id}` now also accept an *optional* auth token (`get_current_user_optional`) and set `is_saved` per item from a single extra query (`_saved_internship_ids()` - one query for a whole page, not one per item) - `false` for anonymous requests, never an error, per the explicit requirement that browsing must never require auth.

Frontend: `SaveButton` (`frontend/components/SaveButton.tsx`) is a small Client Component using Clerk's `useAuth().getToken()` to call the backend directly; an anonymous click opens Clerk's sign-in modal instead of erroring. On `InternshipCard`, the button previously would have had to nest inside the card's own link to the detail page - instead the card uses the "stretched link" pattern (the title `<Link>` gets `after:absolute after:inset-0` to make the whole card clickable, while `SaveButton` sits alongside it with `relative z-10`), avoiding an invalid/inaccessible nested interactive element. Both `SaveButton` instances are deliberately styled as an outlined, muted button - visually secondary to the solid dark Apply button on every card and the detail page, per the explicit "don't make Save more prominent than Apply" requirement.

### Saved Internship Lifecycle

No new mechanism was needed here - it falls directly out of the existing design. `GET /me/saved` joins each `SavedInternship` through to its live `Internship` row, so `is_active` (and everything else) always reflects the current scraper-maintained state, never a stale copy. `InternshipCard` gained a "No longer active" badge (alongside the existing "New" badge) so this is visible wherever the card is rendered, including `/saved`. The user can always unsave an inactive internship (the DELETE endpoint doesn't care about `is_active`); nothing auto-deletes a save when its internship goes inactive, and if the same posting reappears (`is_active` flips back to `true` via the existing scraper lifecycle - unchanged, see Phase 7), the save is still there and reflects it immediately, no special-casing required.

### Notifications

```text
scraper (existing, unchanged)
    v
generate_new_match_events()        - eligibility, idempotent insert
generate_saved_inactive_events()   - eligibility, idempotent insert
    v
send_pending_notifications()       - cadence-gated delivery via Resend
```

All three live in `backend/services/notifications.py` and run as one more step appended to the existing `.github/workflows/scraper.yml`, after the scraper - deliberately not a second scheduler or server (the task's own explicit constraint). `if: always()` on that step means it still runs even if the scraper step reported a hard failure for one company - the notification step operates entirely off already-committed database state, and 15 companies' worth of valid new data shouldn't go un-notified because a 16th company's site was briefly down.

**New match eligibility** (`generate_new_match_events`): for every user with notifications enabled, finds active internships matching their category/industry/location filters *and* first discovered after their preference row was created - never retroactively notifying about internships that already existed when someone signed up or changed their preferences (an explicit requirement, and covered by `tests/test_notifications.py::test_internship_older_than_preference_does_not_notify`).

**Saved-internship-inactive eligibility** (`generate_saved_inactive_events`): every saved internship that's currently `is_active=False` gets an eligibility row, regardless of notification preference (the send step gates on preference, not this one - see below).

**Notification idempotency** is a database constraint, not application bookkeeping: `notification_events` has `UNIQUE(user_id, internship_id, event_type)` (migration `ae99487d261d`), and every insert goes through Postgres's `ON CONFLICT DO NOTHING`. Re-running the whole module - a retried GitHub Actions workflow, a manual re-run, the same scraper cycle somehow firing twice - inserts zero new rows for anything already generated, by construction. This was verified for real, not just asserted: `tests/test_notifications.py` calls `generate_new_match_events`/`generate_saved_inactive_events` two and three times in a row and asserts the count stays at exactly one row, and a manual end-to-end script (see "Problems Encountered" in this phase's completion report) exercised the same idempotency against the real local Postgres instance before any of this shipped.

**Delivery cadence** (`send_pending_notifications`): a user's `frequency` preference controls *when* their already-eligible events get emailed, not whether eligibility is tracked. `immediate` is always due; `daily`/`weekly` compare `now - last_notified_at` against the interval. All of a user's currently-PENDING events (which may mix new-match and saved-inactive reasons) are batched into a single digest email per send, even for `immediate` - since this job only ever runs on the scraper's own 6-hour cadence (there is no separate always-on server that could deliver sooner), "immediate" in practice means "on the next scraper run," and batching avoids sending someone five separate emails for five things discovered in the same run. A user with `email_enabled=False` or `frequency=off` is skipped entirely at send time; their events stay `PENDING` and become eligible for delivery automatically if they re-enable notifications later - nothing is lost, nothing is force-flushed.

A failed send (`EmailSendError`) marks every event in that attempt `FAILED` with a truncated `error_message`, never `SENT` - `tests/test_notifications.py::test_failed_email_marks_events_failed_not_sent` asserts this directly, including that `sent_at` stays `None`. A failed digest is not retried by this run (the next scheduled run will pick up any *new* eligible events, but the failed ones stay `FAILED`, visible for manual investigation, rather than being silently retried into a potential duplicate).

### Email Provider

**Resend**, behind `backend/services/email.py`'s single `send_email()` function - the only place in the codebase that talks to Resend's API. Raises `EmailSendError` on any failure (network error, non-2xx response) rather than swallowing it; callers (`notifications.py`) are responsible for recording that failure against the relevant `NotificationEvent` rows. Verified against the real Resend API during development (not just mocked): a request to an unverified arbitrary address was correctly rejected with Resend's own validation error, and a request to Resend's documented test address (`delivered@resend.dev`) succeeded end-to-end, including through the full `generate_*` → `send_pending_notifications` pipeline against real local Postgres data.

**Domain limitation, stated plainly**: this project has no verified custom domain (deliberately - see Phase 6 "Domain," never purchased). Without one, Resend's free tier only delivers to the account owner's own email address, not arbitrary signed-up users. The notification pipeline itself is fully built, tested, and idempotent regardless of this; real delivery to real users is gated on adding a verified domain in a future phase, and is documented as a current limitation rather than glossed over.

### Environment Variables (new)

| Variable | Where | Purpose |
|---|---|---|
| `CLERK_JWKS_URL`, `CLERK_SECRET_KEY` | Backend (`.env`, Render) | Independent session verification + one-time email lookups |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY` | Frontend (`frontend/.env.local`, Vercel) | Clerk's own Next.js SDK - a separate use of the secret key from the backend's, per "Authentication" above |
| `RESEND_API_KEY`, `NOTIFICATIONS_FROM_EMAIL` | Backend (`.env`, Render, GitHub Actions secrets) | Email sending - needed by both the live API process (not currently, but kept alongside other backend secrets) and the GitHub Actions notification step |

`CORS_ALLOWED_ORIGINS`/`allow_methods` on the FastAPI app were reviewed and updated: the API was GET-only before this phase (a read-only API), and now needs `POST`/`PUT`/`DELETE` for the save/preferences endpoints - previously this would have silently CORS-blocked every new endpoint from the browser.
