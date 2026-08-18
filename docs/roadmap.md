# Development Roadmap

This roadmap defines the intended build order. Phases should generally be completed sequentially — later phases (especially 7 and 8) are intentionally deferred until the MVP (Phases 0–6) is functional.

## Phase 0 — Foundation

**Goal:** Establish product and technical direction before writing implementation code.

**Key Tasks:**
- Write PRD (`docs/PRD.md`)
- Write architecture documentation (`docs/architecture.md`)
- Write this roadmap (`docs/roadmap.md`)
- Write project README
- Create environment/config scaffolding (`.gitignore`, `.env.example`, `requirements.txt`)

**Definition of Done:** Docs and config files exist, are accurate to the current (empty) implementation state, and give a clear, shared understanding of what will be built and in what order.

## Phase 1 — Database

**Goal:** Design and stand up the persistent data layer.

**Key Tasks:**
- Set up local PostgreSQL instance/connection
- Design schema (companies, internships, and fields needed for duplicate detection)
- Define SQLAlchemy models matching the schema
- Set up a migration tool/workflow (e.g., Alembic)
- Load minimal test/seed data for development

**Definition of Done:** Schema is defined and versioned, SQLAlchemy models match the schema, migrations run cleanly against a fresh database, and seed data can be inserted and queried.

## Phase 2 — Scraping MVP

**Goal:** Prove the end-to-end scraping pipeline with a single company.

**Key Tasks:**
- Build `base_scraper.py` shared interface
- Build one company scraper on top of it (`scrapers/companies/`)
- Extract internship listing data relevant to business roles
- Normalize extracted data into the internal schema
- Store normalized data in PostgreSQL
- Implement duplicate detection logic

**Definition of Done:** Running the single company scraper end-to-end produces correctly normalized, deduplicated internship records in PostgreSQL, verified manually.

## Phase 3 — Backend

**Goal:** Expose stored internship data over an API.

**Key Tasks:**
- Set up FastAPI project structure
- Build internship list/detail endpoints
- Implement keyword search
- Implement filtering (category, company, location)
- Implement pagination

**Definition of Done:** API endpoints return correct, paginated, filterable/searchable internship data from PostgreSQL, with basic manual or automated testing.

## Phase 4 — Frontend

**Goal:** Give users a way to browse and search internships.

**Key Tasks:**
- Set up Next.js project structure
- Build internship listing page
- Build internship detail page
- Build search UI
- Build filter UI

**Definition of Done:** A user can load the site, search/filter internships, view details, and click through to the original application link — backed by the live API.

## Phase 5 — Multi-Company Scraping

**Goal:** Scale the scraping pipeline beyond a single company.

**Note:** A small slice of this phase (Phase 2B) already happened early, as a validation step right after the first scraper: two more Greenhouse companies were added, scraper behavior was standardized into a shared `GreenhouseScraper`, per-listing error isolation was confirmed across companies, and logging summaries were verified against real runs. What remains here is scaling to companies beyond Greenhouse (e.g. Workday) and tracking metrics over time.

**Key Tasks:**
- Add additional company scrapers, including non-Greenhouse ATSs (e.g. Workday, requiring Playwright)
- ~~Standardize scraper behavior/conventions across companies~~ — done in Phase 2B via `GreenhouseScraper`
- ~~Add error handling per scraper (isolated failures)~~ — done in `BaseScraper` (Phase 2), confirmed across companies in Phase 2B
- ~~Add logging~~ — done in `BaseScraper` (Phase 2)
- Track basic scraping metrics over time (success/failure rate, listings found per run, persisted rather than just logged)

**Definition of Done:** Multiple company scrapers run independently, failures in one do not affect others, and scraping outcomes are logged and measurable.

## Phase 6 — Automation

**Goal:** Remove the need to manually trigger scraping.

**Key Tasks:**
- Configure scheduled scraping via `scheduler.py`
- Set up GitHub Actions workflow to run scraping on a schedule
- Ensure scraped data automatically updates PostgreSQL
- Add basic monitoring/alerting for failed runs

**Definition of Done:** Internship data refreshes automatically on a schedule without manual intervention, with visibility into failures.

## Phase 7 — Product Features

**Goal:** Add user-facing product depth beyond the core MVP.

**Key Tasks:**
- User accounts / authentication
- Saved internships
- Notifications (e.g., email alerts for new matches)
- Application tracking

**Definition of Done:** Users can create accounts, save internships, receive notifications, and track application status — layered on top of the working MVP.

## Phase 8 — Intelligence

**Goal:** Add AI-assisted features once the platform has real usage and data.

**Key Tasks:**
- Resume matching
- AI-powered recommendations
- Skill extraction from postings
- Hiring trend analytics

**Definition of Done:** AI features are integrated, evaluated for quality/usefulness, and clearly opt-in/additive to the core search experience.
