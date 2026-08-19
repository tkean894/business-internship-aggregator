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

## Phase 5 — Multi-Company Scraping (Complete)

**Goal:** Scale the scraping pipeline beyond a single company.

**Note:** A small slice of this phase (Phase 2B) already happened early, as a validation step right after the first scraper: two more Greenhouse companies were added, scraper behavior was standardized into a shared `GreenhouseScraper`, per-listing error isolation was confirmed across companies, and logging summaries were verified against real runs. The rest of this phase's scope (non-Greenhouse ATS support, metrics over time) was completed later — internally tracked as "Phase 7" in project instructions at the time, since it happened after Phase 6 (Automation & Production Deployment) — and went further than this phase's original scope into classification-quality and data-validation hardening driven by the newly-expanded real dataset. See `docs/architecture.md` ("Implementation Notes (Phase 7 — Scraper Expansion & Data Quality)") for full detail.

**Key Tasks:**
- ~~Add additional company scrapers, including non-Greenhouse ATSs~~ — done: `WorkdayScraper` (Abbott Laboratories) added alongside 4 new Greenhouse companies (Rocket Lab, SpaceX, Red Ventures, SpotHopper), bringing the total to 8 companies across 2 ATS platforms. Workday's public JSON API made Playwright unnecessary here (kept as a dependency for a future ATS without one).
- ~~Standardize scraper behavior/conventions across companies~~ — done in Phase 2B via `GreenhouseScraper`; extended with `WorkdayScraper` plus shared `http_utils`/`text_utils` modules so both ATS integrations use one retry/backoff policy and one set of cleanup helpers
- ~~Add error handling per scraper (isolated failures)~~ — done in `BaseScraper` (Phase 2), confirmed across companies in Phase 2B, extended to distinguish fetch/database/per-listing failure classes
- ~~Add logging~~ — done in `BaseScraper` (Phase 2)
- ~~Track basic scraping metrics over time~~ — done: a persisted `scraper_runs` table (not just logs) records every run's status, timing, and counts
- Additional, beyond this phase's original scope: classification-quality fixes (word-boundary matching, a new `Sales` category, broadened technical-role exclusions) and pre-insert data validation, both driven by real false positives/gaps the expanded company set actually surfaced

**Definition of Done:** Multiple company scrapers run independently, failures in one do not affect others, and scraping outcomes are logged and measurable. ✅ Verified against production: 8 companies, 2 ATS platforms, persisted `scraper_runs` metrics, zero duplicate `dedupe_key`s.

## Phase 6 — Automation & Production Deployment (Complete)

**Goal:** Remove the need to manually trigger scraping, and make the application publicly accessible.

This phase grew from its original scope (automation only) to include full production deployment, since automated scraping is only meaningful against a live, publicly reachable application. See `docs/architecture.md` ("Production Architecture") and the README's "Live Application" / "Production" sections for full detail.

**Key Tasks:**
- ~~Configure scheduled scraping via `scheduler.py`~~ — done; also added per-company error isolation and inactive-listing lifecycle detection (previously missing despite being listed as complete)
- ~~Set up GitHub Actions workflow to run scraping on a schedule~~ — done (`.github/workflows/scraper.yml`, every 6h + manual `workflow_dispatch`)
- ~~Ensure scraped data automatically updates PostgreSQL~~ — done, against a managed production database (Neon)
- ~~Add basic monitoring/alerting for failed runs~~ — GitHub Actions run status/logs and Render's deploy/service logs serve this at MVP scale; no paid monitoring platform added
- Deploy managed PostgreSQL (Neon), FastAPI (Render), and Next.js (Vercel)
- Apply production schema via Alembic only (no manual DDL) and populate real scraped data
- Restrict production CORS to the deployed frontend origin (no wildcard)
- Verify security posture: no secrets committed (checked across full git history), `.env` files gitignored, credentials stored only as Render/Vercel/GitHub Actions environment configuration

**Definition of Done:** Internship data refreshes automatically on a schedule without manual intervention, with visibility into failures, **and** the application is publicly accessible end-to-end (Career Sites → Scrapers → GitHub Actions → Neon → FastAPI → Next.js → User) — verified live, not just locally.

## Phase 7 — Dataset Expansion & Product Polish (Complete)

**Goal:** Increase the platform's actual usefulness (dataset breadth, industry diversity, discoverability) before layering on accounts/notifications/AI - this phase didn't exist in the original Phase 0-8 plan above; it was inserted here (renumbering the two phases that follow) once Phase 5/6's completion made clear that dataset depth and product usability, not new infrastructure, were the real gap.

**Key Tasks:**
- ~~Expand the company dataset~~ — done: 8 → 16 companies (Greenhouse: 7, Workday: 8, Lever: 1), each individually verified for real, currently-open business-relevant postings, reaching 118 active internships (target was 100+)
- ~~Expand industry diversity~~ — done: Technology, Financial Services, Aerospace, Healthcare, Investment Management, Insurance, Manufacturing, Energy, Food & Beverage, Consulting (was tech/aerospace-only)
- ~~Expand ATS coverage where justified~~ — done: Lever added (`scrapers/lever.py`), justified by a real, verified company (HCVT) rather than added for architectural completeness alone
- ~~Add company industry metadata~~ — done (`Company.industry`, migration `dda83df7adaa`)
- ~~Improve classification~~ — done: new Real Estate category, several Finance/Accounting keyword additions, a real regex bug fix (underscore word-boundary), broadened technical exclusions - all driven by real observed titles, not speculative
- ~~Improve freshness visibility~~ — done: `posted_date`-vs-`first_seen_at` distinction surfaced honestly throughout the frontend, "New" badge
- ~~Improve search/filter UX~~ — done: industry filter, `first_seen_desc` sort, category-pill and company-list discovery pages
- ~~Improve homepage/product presentation~~ — done: hero copy, live stats, "Recently Added" section, contextual empty states

**Definition of Done:** ✅ A substantially broader, more diverse dataset (verified against production: 16 companies, 118 active internships, 10 industries), improved classification accuracy on real data, and a frontend that functions as an actual discovery product rather than a raw search form — all without accounts, saved jobs, notifications, or AI.

## Phase 8 — Product Features (Complete)

**Goal:** Add user-facing product depth beyond the core MVP. Internally tracked as "Phase 9" in project instructions at the time (numbering had drifted from this document after Phase 7 was inserted - see that phase's note); implemented here since it matches this slot's original scope.

**Key Tasks:**
- ~~User accounts / authentication~~ — done via Clerk (see `docs/architecture.md` "Authentication"); FastAPI verifies every request independently against Clerk's JWKS rather than trusting the frontend
- ~~Saved internships~~ — done (`saved_internships` table, `UNIQUE(user_id, internship_id)`, Save/Saved button on cards and detail pages, `/saved` page)
- ~~Notifications~~ — done: new-match and saved-internship-inactive email alerts, idempotent via a `UNIQUE(user_id, internship_id, event_type)` constraint on `notification_events`, delivered through Resend as part of the existing GitHub Actions scraper workflow (no second scheduler)
- Application tracking — not implemented; a reasonable candidate for a future phase, not required for this one's core goal

**Definition of Done:** ✅ Users can create accounts, sign in/out, save internships, and configure notification preferences (categories/industries/locations/frequency); anonymous browsing is entirely unaffected. Verified against production (see completion report for this phase). Application tracking deliberately deferred.

## Phase 9 — Top 200 Business Internship Company Expansion (Step 1: Registry & Architecture — Complete)

**Goal:** Scale the company dataset from 16 toward ~200 without sacrificing data quality, legitimate/compliant scraping, or maintainability. Internally tracked as "Phase 10" in project instructions at the time (numbering had drifted from this document again after Phase 7 was inserted - see that phase's note); implemented here since "Intelligence" (below) had not yet started and this phase's own instructions were explicit that only Step 1 — research, registry, and architecture, not scraper implementation — was in scope.

**Key Tasks (Step 1 only):**
- ~~Research and document candidate companies toward the ~200 target~~ — done: `scrapers/company_registry.py`, 51 companies total (16 already implemented + 35 new candidates), prioritizing business-relevant roles/industries over raw company size
- ~~Design a centralized company registry~~ — done: a standalone module (not a DB schema change - `backend/models/company.py` was re-inspected and intentionally left untouched, see `docs/architecture.md` "Implementation Notes (Phase 10)" for why), tracking ATS platform/identifiers, tier, status, and research notes per company independent of whether a scraper exists yet
- ~~ATS research with compliance verification~~ — done, applying the same public/unauthenticated-endpoint bar as every prior ATS integration; companies with only indirect or aggregator-sourced evidence are marked `needs_review` rather than guessed at (the Phase 8 Lever precedent)
- ~~Build a prioritization/tiering system~~ — done: 4 tiers (implemented / ready-to-implement with confirmed identifiers / researched-needs-confirmation / needs-review-or-excluded), documented in `docs/architecture.md`
- Full 200-company scraper rollout — deliberately **not** started; this step is registry and architecture only, pending approval

**Definition of Done:** ✅ Registry module exists and is tested (`tests/test_company_registry.py`, 8 tests, all passing alongside the existing 77 — 85 total, zero regressions), can represent all 16 currently-implemented companies with values cross-checked against their real scraper configs, and documents a clear, compliant path toward 200 without adding a single new scraper, frontend change, or production schema change. Full company-by-company detail and next-step recommendation in this step's completion report. Stopped here per explicit instruction, pending approval of the registry and company list before any scraper implementation begins.

**Step 2 (Tier 2 Company Scraper Expansion — Complete):** Took the 14 Tier 2 (`ready`) companies from the registry, live-verified each one's ATS access independently (not trusting Step 1's research), and implemented 10 of them: Barclays, Federal Reserve Bank of New York, CIBC, Piper Sandler Companies, Texas Capital Bank, PwC, Guidehouse, GE Aerospace, The Boeing Company, and The Walt Disney Company - each a small `WorkdayScraper` config reusing the existing shared ATS logic, no new scraper classes. `scrapers/workday.py` gained two generalized, config-driven fallback modes (a bounded `search_text` query; a whole-small-board scan) for tenants lacking a clean `workerSubType` facet, and `scrapers/classification.py`'s `INTERN_TITLE_RE` gained a "summer analyst" synonym after real cross-company evidence showed it's a common finance-internship title with no "intern"/"internship" in it at all. 4 companies (Truist, TD Bank, Verizon, Accenture) were deferred with documented, evidence-based reasons rather than forced. Production companies: 16 → 26. See `docs/architecture.md` ("Implementation Notes (Phase 10 Step 2)") and this step's completion report for full verification, local-database, and production-deployment detail.

## Phase 10 — Intelligence

**Goal:** Add AI-assisted features once the platform has real usage and data.

**Key Tasks:**
- Resume matching
- AI-powered recommendations
- Skill extraction from postings
- Hiring trend analytics

**Definition of Done:** AI features are integrated, evaluated for quality/usefulness, and clearly opt-in/additive to the core search experience.
