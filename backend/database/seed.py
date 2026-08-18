"""
TEST / SEED DATA — for local development and verification only.

Every company and internship created here is fictional. Do not treat
any record produced by this script as a real posting.

Run with:
    py -m backend.database.seed
"""

from __future__ import annotations

from datetime import date, timedelta

from backend.database.session import SessionLocal
from backend.database.utils import compute_dedupe_key
from backend.models import Company, Internship, InternshipCategory

TEST_COMPANIES = [
    {
        "name": "Example Corporation (TEST DATA)",
        "slug": "example-corporation",
        "career_url": "https://careers.example.test",
        "website_url": "https://www.example.test",
    },
    {
        "name": "Northbridge Consulting Group (TEST DATA)",
        "slug": "northbridge-consulting-group",
        "career_url": "https://careers.northbridgeconsulting.test",
        "website_url": "https://www.northbridgeconsulting.test",
    },
    {
        "name": "Cardinal Retail Co. (TEST DATA)",
        "slug": "cardinal-retail-co",
        "career_url": "https://careers.cardinalretail.test",
        "website_url": "https://www.cardinalretail.test",
    },
]

# (company_slug, title, category, location, employment_type, days_ago_posted)
TEST_INTERNSHIPS = [
    ("example-corporation", "Business Analyst Intern", InternshipCategory.BUSINESS_ANALYTICS, "Indianapolis, IN", "Internship", 5),
    ("example-corporation", "Finance Intern", InternshipCategory.FINANCE, "Indianapolis, IN", "Internship", 10),
    ("example-corporation", "Marketing Intern", InternshipCategory.MARKETING, "Chicago, IL", "Internship", 2),
    ("northbridge-consulting-group", "Consulting Summer Intern", InternshipCategory.CONSULTING, "Chicago, IL", "Internship", 7),
    ("northbridge-consulting-group", "Strategy Intern", InternshipCategory.STRATEGY, "Remote", "Internship", 14),
    ("cardinal-retail-co", "Supply Chain Intern", InternshipCategory.SUPPLY_CHAIN, "Columbus, OH", "Internship", 3),
    ("cardinal-retail-co", "Human Resources Intern", InternshipCategory.HUMAN_RESOURCES, "Columbus, OH", "Internship", 20),
    ("cardinal-retail-co", "Operations Intern", InternshipCategory.OPERATIONS, "Columbus, OH", "Internship", 1),
]


def seed() -> None:
    session = SessionLocal()
    try:
        slug_to_company: dict[str, Company] = {}
        for data in TEST_COMPANIES:
            company = session.query(Company).filter_by(slug=data["slug"]).one_or_none()
            if company is None:
                company = Company(**data)
                session.add(company)
                session.flush()  # assign company.id so it can be used in dedupe_key below
            slug_to_company[data["slug"]] = company

        created = 0
        for slug, title, category, location, employment_type, days_ago in TEST_INTERNSHIPS:
            company = slug_to_company[slug]
            dedupe_key = compute_dedupe_key(company.id, title, location)

            if session.query(Internship).filter_by(dedupe_key=dedupe_key).one_or_none() is not None:
                continue  # already seeded — duplicate prevention working as intended

            slug_title = title.lower().replace(" ", "-")
            internship = Internship(
                company_id=company.id,
                title=title,
                description=f"TEST DATA: fictional posting for '{title}' at {company.name}.",
                category=category,
                location=location,
                employment_type=employment_type,
                application_url=f"{company.career_url}/jobs/{slug_title}",
                source_url=f"{company.career_url}/jobs/{slug_title}",
                posted_date=date.today() - timedelta(days=days_ago),
                dedupe_key=dedupe_key,
            )
            session.add(internship)
            created += 1

        session.commit()
        print(
            f"Seed complete: {len(TEST_COMPANIES)} companies ensured, "
            f"{created} new internship(s) created "
            f"({len(TEST_INTERNSHIPS) - created} already present)."
        )
    finally:
        session.close()


if __name__ == "__main__":
    seed()
