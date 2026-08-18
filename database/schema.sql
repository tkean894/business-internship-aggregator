-- =====================================================================
-- Business Internship Aggregator — PostgreSQL Schema
-- =====================================================================
-- Phase 1 (Database Foundation). Defines the two core tables used by
-- the scraping pipeline and (later) the API: companies and internships.
--
-- This file is the source-of-truth reference for the schema. The
-- Alembic migration in alembic/versions/ creates the same structure
-- and SQLAlchemy models in backend/models/ mirror it in Python.
--
-- Design principles:
--   - Companies are never hard-deleted; use is_active instead, so
--     historical internship data is never orphaned or lost.
--   - Internships track their own lifecycle (first_seen_at /
--     last_seen_at / is_active) so repeated scraper runs can detect
--     new, existing, and disappeared postings.
--   - Duplicate prevention relies on a computed `dedupe_key` rather
--     than raw URLs or titles alone — see the comment block below.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Enum: fixed set of business-relevant internship categories for MVP.
-- Adding a new category later requires an ALTER TYPE migration; this
-- is an acceptable tradeoff given the list is small and stable.
-- ---------------------------------------------------------------------
CREATE TYPE internship_category AS ENUM (
    'Product Management',
    'Business Analytics',
    'Finance',
    'Accounting',
    'Consulting',
    'Marketing',
    'Operations',
    'Supply Chain',
    'Strategy',
    'Human Resources',
    'Other'
);

-- ---------------------------------------------------------------------
-- companies
-- One row per company whose career site is monitored. A single field
-- per company for MVP — no separate category/tag tables are needed.
-- ---------------------------------------------------------------------
CREATE TABLE companies (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    slug          VARCHAR(255) NOT NULL,          -- normalized identifier, e.g. "deloitte"; used for scraper lookup and to prevent duplicate company rows
    career_url    TEXT NOT NULL,
    website_url   TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,  -- soft-disable a company instead of deleting it
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_companies_slug UNIQUE (slug)
);

CREATE INDEX idx_companies_is_active ON companies (is_active);

-- ---------------------------------------------------------------------
-- internships
-- One row per internship posting, scoped to a single company.
-- ---------------------------------------------------------------------
CREATE TABLE internships (
    id                    SERIAL PRIMARY KEY,
    company_id            INTEGER NOT NULL REFERENCES companies (id) ON DELETE RESTRICT,
    title                 VARCHAR(500) NOT NULL,
    description           TEXT,
    category              internship_category NOT NULL DEFAULT 'Other',
    location              VARCHAR(255),
    employment_type       VARCHAR(50) NOT NULL DEFAULT 'Internship',
    application_url       TEXT NOT NULL,
    source_url            TEXT NOT NULL,          -- the specific career-site page the scraper read this listing from
    posted_date           DATE,
    application_deadline  DATE,
    is_active             BOOLEAN NOT NULL DEFAULT TRUE,  -- flipped to false when a scraper run no longer finds this posting
    first_seen_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Duplicate-prevention key. See "Deduplication Strategy" below.
    dedupe_key            VARCHAR(64) NOT NULL,

    CONSTRAINT uq_internships_dedupe_key UNIQUE (dedupe_key)
);

CREATE INDEX idx_internships_company_id  ON internships (company_id);
CREATE INDEX idx_internships_category    ON internships (category);
CREATE INDEX idx_internships_is_active   ON internships (is_active);
CREATE INDEX idx_internships_posted_date ON internships (posted_date);
CREATE INDEX idx_internships_source_url  ON internships (source_url);

-- ---------------------------------------------------------------------
-- Keep updated_at current automatically on any row update, for both
-- tables. Application code never needs to remember to set it.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_companies_updated_at
BEFORE UPDATE ON companies
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_internships_updated_at
BEFORE UPDATE ON internships
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =====================================================================
-- Deduplication Strategy
-- =====================================================================
-- `dedupe_key` is a sha256 hex digest computed by the application layer
-- (backend/database/utils.py, compute_dedupe_key) from:
--
--     company_id + normalized(title) + normalized(location)
--
-- Normalization = lowercase, strip, collapse internal whitespace, strip
-- punctuation. This logic lives in Python (not SQL) so the exact same
-- normalization is used whether the caller is the scraper's insert
-- path or any future re-check/cleanup logic.
--
-- Why not just UNIQUE(application_url) or UNIQUE(source_url)?
--   Many company career sites / ATS platforms (Workday, Greenhouse,
--   etc.) append session or tracking query parameters to listing URLs,
--   so the same real-world posting can legitimately produce different
--   URLs across scraper runs. Relying on the raw URL would create
--   false "new" postings on every run.
--
-- Why not just UNIQUE(company_id, title)?
--   Large companies commonly post multiple internships with an
--   identical generic title (e.g. "Finance Intern") for different
--   teams or offices. Title + company alone would incorrectly
--   collapse those distinct postings into one row.
--
-- Combining company + normalized title + normalized location is a
-- low-cost heuristic that removes the overwhelming majority of real
-- duplicates at MVP scale. It is not perfect (two genuinely distinct
-- postings with identical title/location would collide), but fuzzy
-- matching or ML-based dedup is explicitly out of scope for now.
-- =====================================================================
