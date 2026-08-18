# Product Requirements Document

## Product Name
Business Internship Aggregator

## Problem

Business students looking for internships face a fragmented search process. Relevant roles in Product Management, Business Analytics, Finance, Accounting, Consulting, Marketing, Operations, Supply Chain, Strategy, and Human Resources are scattered across hundreds of individual company career sites, each with different layouts, filters, and posting cadences. There is no single place to search across them.

Most existing internship aggregators (e.g., tools built by and for computer science students) are optimized for software engineering roles — filtering by tech stack, LeetCode-style tagging, or engineering-specific keywords. Business students are left manually checking dozens of company career pages on a recurring basis, with no efficient way to discover new postings as they go live.

## Target Users

**Primary user:** Undergraduate and graduate business students actively searching for internships in one or more business functions (finance, consulting, marketing, operations, etc.).

**Secondary users:**
- Career services staff at universities who want to point students to a centralized, business-relevant internship resource.
- Early-career job switchers or MBA students exploring business internships/rotational programs.

## Problem Statement

Business students need a single, searchable platform that continuously and automatically aggregates internship postings from company career pages, specifically curated for business-relevant roles, so they don't have to manually monitor dozens of individual company websites.

## Value Proposition

A business-focused internship aggregator saves students time and reduces missed opportunities by:
- Centralizing postings from many companies into one searchable interface.
- Filtering specifically for business-relevant functions instead of being dominated by engineering roles.
- Surfacing new postings automatically and consistently, rather than relying on students to remember to check each company's site.

## MVP Scope

### In Scope
1. Automated internship collection from company career websites (via scrapers).
2. Data normalization into a consistent internship record format.
3. Persistent storage in PostgreSQL.
4. Duplicate detection so the same posting isn't shown multiple times.
5. A basic REST API exposing internship data.
6. A searchable web interface for browsing internships.
7. Basic filtering (e.g., by function/category, company, location).

### Explicitly Out of Scope for MVP
- User accounts / authentication
- AI resume matching
- Personalized recommendations
- Email notifications
- Application tracking
- Advanced analytics

These are documented as future features (see below) and should not be implemented until the MVP is functional and validated.

## User Stories

- As a business student, I want to search internships by keyword (e.g., "marketing") so I can quickly find roles relevant to my interests.
- As a business student, I want to filter internships by category (Finance, Consulting, Marketing, etc.) so I don't have to scroll through irrelevant postings.
- As a business student, I want to filter internships by company or location so I can narrow results to what's realistic for me.
- As a business student, I want to see when a posting was first detected so I know how fresh it is.
- As a business student, I want to click through directly to the original application page so I can apply without friction.
- As a business student, I want to trust that listings aren't duplicated or stale so I don't waste time on dead links.
- As a career services staff member, I want to point students to a single link that stays current so I don't have to maintain my own list of company career pages.

## Functional Requirements

- The system must scrape internship postings from a defined list of company career pages.
- The system must normalize scraped postings into a consistent schema (title, company, category, location, description, URL, date posted/detected).
- The system must store normalized postings in PostgreSQL.
- The system must detect and prevent duplicate postings (e.g., same role re-scraped, or same posting appearing under slightly different text).
- The system must expose an API for retrieving internship listings, including search and filter parameters.
- The system must provide a web interface where users can search internships by keyword.
- The system must provide a web interface where users can filter internships by category, company, and/or location.
- The system must link each listing back to the original company application page.
- The system must mark or remove postings that are no longer active, once that capability exists (best-effort for MVP).

## Non-Functional Requirements

- **Reliability:** Scrapers should fail gracefully — a single broken scraper (e.g., due to a career site redesign) must not crash the overall pipeline or take down other scrapers.
- **Performance:** API search/filter queries should return results in well under 1 second for MVP-scale data (hundreds to low thousands of listings).
- **Maintainability:** Scraper logic must be isolated per company behind a shared base interface, so adding or fixing a company scraper doesn't require touching unrelated code.
- **Security:** No credentials, API keys, or secrets committed to source control; all configuration via environment variables.
- **Scalability:** Architecture should support adding more companies and more listings over time without requiring a redesign, but should not be over-engineered for scale the MVP doesn't need (no Kubernetes, no microservices).

## Success Metrics

- Number of companies actively monitored.
- Number of active (currently open) internship listings in the database.
- Number of new internships detected per scraping run/week.
- Scraper success rate (successful runs vs. failed runs per company).
- Duplicate rate (duplicates caught vs. total postings processed).
- Search/filter usage (queries run against the platform).
- Application-link click-through rate (clicks on "Apply" / outbound links).

## Future Features (Post-MVP)

- User accounts and authentication
- Saved/bookmarked internships
- Email alerts for new matching postings
- Personalized search preferences
- Application tracking (status per internship applied to)
- Resume matching
- AI-powered recommendations
- Salary analytics
- Hiring trend analytics
- Browser extension

These are intentionally deferred until the MVP (automated collection, storage, search, and filtering) is working and validated.
