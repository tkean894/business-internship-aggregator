from backend.models import InternshipCategory
from scrapers.classification import classify_internship


def test_valid_business_internship_gets_specific_category():
    assert classify_internship("Finance Intern") == InternshipCategory.FINANCE
    assert classify_internship("Accounting Intern (Fall 2026)") == InternshipCategory.ACCOUNTING
    assert classify_internship("Supply Chain Intern") == InternshipCategory.SUPPLY_CHAIN


def test_technical_internships_are_excluded():
    assert classify_internship("Software Engineer Intern") is None
    assert classify_internship("Research Engineer Intern") is None
    assert classify_internship("Data Scientist Intern") is None
    # Phase 7 additions - aerospace/hardware roles from Rocket Lab/SpaceX.
    assert classify_internship("Avionics Development Intern - Electron") is None
    assert classify_internship("Manufacturing Engineering Intern") is None
    assert classify_internship("Spring 2027 Civil Engineering Internship") is None
    assert classify_internship("RF Test Engineer Intern") is None


def test_non_internship_titles_return_none():
    # "International"/"Internal" must not false-positive on the substring "intern".
    assert classify_internship("International Product Manager") is None
    assert classify_internship("Internal Communications Director") is None
    assert classify_internship("Senior Finance Manager") is None


def test_specific_phrase_outranks_generic_phrase():
    # Real Phase 2 bug: "strategy" (generic) would otherwise beat
    # "market research" (specific) purely due to list order.
    assert classify_internship("Market Research Strategy Intern") == InternshipCategory.BUSINESS_ANALYTICS
    assert classify_internship("Network Strategy Intern") == InternshipCategory.STRATEGY


def test_unmatched_business_internship_falls_back_to_other():
    assert classify_internship("GRC Team Intern") == InternshipCategory.OTHER


def test_sales_category_matches_real_observed_titles():
    assert classify_internship("Business Development Representative Intern") == InternshipCategory.SALES
    assert classify_internship("Commercial Excellence Intern") == InternshipCategory.SALES
    assert classify_internship("Business Development Internship") == InternshipCategory.SALES


def test_sales_keyword_does_not_substring_match_salesforce():
    # Regression test for a real bug found during Phase 7 testing: a
    # plain `"sales" in title.lower()` check matched inside "Salesforce".
    result = classify_internship("Salesforce Administrator Intern")
    assert result != InternshipCategory.SALES
    assert result == InternshipCategory.OTHER  # still a real internship, just uncategorized


def test_learning_and_development_maps_to_human_resources():
    assert classify_internship("Learning & Development Intern") == InternshipCategory.HUMAN_RESOURCES


def test_engineering_intern_exclusion_matches_internship_suffix():
    # "engineering intern" must also match "...Engineering Internship"
    # (the word continues into "-ship"), not just the bare "Intern" form.
    assert classify_internship("Spring 2027 Silicon Engineering Internship/Co-op") is None
    assert classify_internship("Spring 2027 Graduate Engineer Internship/Co-op") is None


def test_business_operations_is_not_excluded_by_engineering_keywords():
    assert classify_internship("Summer 2027 Business Operations Internship/Co-op") == InternshipCategory.OPERATIONS


def test_summer_analyst_is_treated_as_an_internship_title():
    # Phase 10 Step 2: real, live titles from TD Securities, CIBC, and
    # Piper Sandler contain neither "intern" nor "internship" at all.
    assert classify_internship("Investment Banking Summer Analyst (Summer 2026)") == InternshipCategory.FINANCE
    assert classify_internship("2026 Investment Banking Summer Analyst - Global Diversified Industries") == InternshipCategory.FINANCE
    assert classify_internship("Campus Recruiting - 2026 Investment Banking Summer Analyst - Restructuring NY") == InternshipCategory.FINANCE


def test_full_time_analyst_without_summer_is_not_an_internship():
    # "summer analyst" requires both words together - a full-time,
    # post-graduation "Analyst" role must not be swept in.
    assert classify_internship("Investment Banking Analyst") is None
    assert classify_internship("Equity Research Associate - Large Cap Banks") is None
    assert classify_internship("Investment Banking Associate - Chemicals") is None


def test_consultant_noun_maps_to_consulting():
    # Phase 10 Step 6: Marsh McLennan's Oliver Wyman postings are
    # frequently titled with the noun "Consultant" rather than
    # "Consulting" - real, recurring live titles.
    assert classify_internship("Oliver Wyman - Consultant Intern (m/f/d) 2027 - Copenhagen") == InternshipCategory.CONSULTING
    assert classify_internship("OLIVER WYMAN - INTERN CONSULTANT - 2026 - NETHERLANDS") == InternshipCategory.CONSULTING


def test_banking_maps_to_finance():
    # Phase 10 Step 6: real, recurring across two unrelated companies -
    # PNC ("Corporate & Institutional Banking Undergraduate Intern -
    # Commercial & Corporate Banking") and Wells Fargo ("Consumer
    # Banking and Lending Summer Internship", "Commercial Banking Summer
    # Internship") - both previously fell to OTHER.
    assert classify_internship("Corporate & Institutional Banking Undergraduate Intern - Commercial & Corporate Banking") == InternshipCategory.FINANCE
    assert classify_internship("Consumer Banking and Lending Summer Internship") == InternshipCategory.FINANCE


def test_banking_keyword_does_not_override_more_specific_analytics_match():
    # Deliberately did NOT add "capital markets" as its own Finance
    # keyword (see scrapers/classification.py) - it would, as the longer
    # match, override the existing correct "analytics" match on real
    # Wells Fargo postings like this one.
    result = classify_internship("2027 Quantitative Analytics Summer Internship Capital Markets (Masters) - Early Careers")
    assert result == InternshipCategory.BUSINESS_ANALYTICS


def test_software_developer_and_cybersecurity_are_excluded_as_technical():
    # Phase 10 Step 7: real Booz Allen Hamilton postings - "Software
    # Developer" (not caught by the existing "software engineer"
    # keyword) and "Cybersecurity" as one word (not caught by the
    # existing two-word "cyber security" phrase) - were falling to
    # OTHER instead of being excluded as technical roles.
    assert classify_internship("AI Software Developer Intern") is None
    assert classify_internship("University - 2027 Summer Games Software Developer Intern") is None
    assert classify_internship("University - Summer 27, Cybersecurity Analyst Intern") is None
    # The existing two-word phrasing must keep working too.
    assert classify_internship("Intern, Cyber Security") is None


def test_wealth_maps_to_finance():
    # Phase 10 Step 7: real, recurring Citigroup postings ("Wealth -
    # Citigold, Summer Analyst", "Wealth - Private Bank, Summer
    # Analyst") were falling to OTHER despite Wealth Management being
    # an explicit target business function for this platform.
    assert classify_internship("Wealth - Citigold, Summer Analyst, Singapore, 2027") == InternshipCategory.FINANCE
    assert classify_internship("Wealth - Private Bank, Summer Analyst, Hong Kong, 2027") == InternshipCategory.FINANCE


def test_bare_hr_maps_to_human_resources():
    # Phase 10 Step 7: real Kraft Heinz posting titled bare "HR Intern"
    # (not caught by the existing spelled-out "human resources"
    # keyword) was falling to OTHER.
    assert classify_internship("HR Intern") == InternshipCategory.HUMAN_RESOURCES


def test_bare_hr_keyword_has_a_real_word_boundary_not_a_substring_match():
    # "hr" must not fire on a title where those two letters appear
    # embedded inside a longer, unrelated word.
    result = classify_internship("Chromatography Intern")
    assert result != InternshipCategory.HUMAN_RESOURCES


def test_assurance_maps_to_accounting():
    # Phase 10 Step 8: real, recurring PwC postings (Big 4 industry term
    # for audit/attestation services) - previously fell to OTHER.
    assert classify_internship("Intern - Assurance") == InternshipCategory.ACCOUNTING
    assert classify_internship("Assurance Standards Off-Cycle Internship (Feb - Jun 2027)") == InternshipCategory.ACCOUNTING


def test_assurance_keyword_does_not_override_an_equally_specific_finance_match():
    # Regression guard: "financial" and "assurance" are the same length
    # (9 chars) - a title matching both must keep resolving to Finance
    # (found first in CATEGORY_KEYWORDS order) rather than flip to
    # Accounting just because "assurance" appears later in the string.
    result = classify_internship("Financial Services Assurance - Off-Cycle Internship (Jan - Jun 27)")
    assert result == InternshipCategory.FINANCE


def test_singular_operation_maps_to_operations():
    # Phase 10 Step 8: 30 real, recurring Target postings ("Operation
    # Manager Intern" at various Distribution Centers) use the singular
    # "Operation" - the existing "operations"/"ops" keywords require the
    # plural or abbreviated form and missed these entirely.
    assert classify_internship("Operation Manager Intern (Starting Summer 2027) Food Distribution Center - Denton, TX") == InternshipCategory.OPERATIONS
    # The plural form must keep working too.
    assert classify_internship("Operations Manager Intern (Starting Summer 2027) Flow Distribution Center, Hampton, GA") == InternshipCategory.OPERATIONS


def test_legal_maps_to_legal_category():
    # Phase 10 Step 9: real, recurring postings across 9 unrelated
    # companies previously fell to OTHER (or, in one case, Operations).
    assert classify_internship("Legal Intern") == InternshipCategory.LEGAL
    assert classify_internship("Intern, Group Legal") == InternshipCategory.LEGAL
    assert classify_internship("Law Internship (Stage)") == InternshipCategory.LEGAL
    assert classify_internship("Internship Litigation Team - Non Performing Exposures Management (f/m/x)") == InternshipCategory.LEGAL


def test_legal_keyword_does_not_collide_with_lawyer_or_flawed_substrings():
    # "law" must word-boundary match, not substring-match inside an
    # unrelated word.
    result = classify_internship("Flawless Execution Intern")
    assert result != InternshipCategory.LEGAL


def test_auditor_maps_to_accounting():
    # Phase 10 Step 9: real PwC "Junior Auditor (Intern)" postings - the
    # existing "audit" keyword requires a trailing word boundary and
    # doesn't match the "-or" noun form.
    assert classify_internship("Junior Auditor (Intern) - 4 months") == InternshipCategory.ACCOUNTING


def test_auditor_keyword_does_not_override_a_longer_operations_match():
    # Regression guard: a real Disney posting already correctly resolves
    # to Operations via the longer "operations" keyword (10 chars) and
    # must keep doing so now that "auditor" (7 chars) also matches.
    result = classify_internship("Quality Operations System Auditor Intern, Spring 2027")
    assert result == InternshipCategory.OPERATIONS


def test_hrbp_maps_to_human_resources():
    assert classify_internship("HRBP Intern (Jan-Jun 2027)") == InternshipCategory.HUMAN_RESOURCES


def test_purchasing_maps_to_supply_chain():
    # Phase 10 Step 9: real P&G/GM postings use "Purchasing", the
    # standard retail/manufacturing synonym for procurement.
    assert classify_internship("Purchasing Intern") == InternshipCategory.SUPPLY_CHAIN
    assert classify_internship("Purchasing Student Intern") == InternshipCategory.SUPPLY_CHAIN


def test_business_intelligence_maps_to_business_analytics():
    assert classify_internship("Business Intelligence & Data Analysis Internship") == InternshipCategory.BUSINESS_ANALYTICS


def test_credit_maps_to_finance():
    assert classify_internship("Credit Intern") == InternshipCategory.FINANCE


def test_credit_keyword_does_not_override_more_specific_matches():
    # Regression guard: real postings that already resolve correctly via
    # a longer keyword must keep doing so.
    assert classify_internship("Early Career Intern - Real Estate (Equity & Credit)") == InternshipCategory.REAL_ESTATE
    assert classify_internship("Corporate & Institutional Banking Undergraduate Intern - Tax Credit") == InternshipCategory.FINANCE


def test_store_leadership_maps_to_operations():
    # Phase 10 Step 9: 80 real, recurring Target "Store Executive Intern
    # (Store Leadership Intern)" postings, one per store location - by
    # far the single largest fix in this phase.
    assert classify_internship("Store Executive Intern (Store Leadership Intern) - Denver, CO (Starting Summer 2027)") == InternshipCategory.OPERATIONS
    # A minority of the 80 use the plural "Stores Executive" - "store
    # leadership" alone (present in all 80 via the parenthetical) covers
    # this case too.
    assert classify_internship("Stores Executive Internship (Store Leadership Intern) - Omaha, NE (Starting Summer 2027)") == InternshipCategory.OPERATIONS


def test_technical_and_vocational_leakage_is_excluded():
    # Phase 10 Step 9: a full-dataset audit of OTHER found skilled-trade
    # and engineering-discipline postings that the existing exclusion
    # list didn't catch, either because the title uses "Engineering" as
    # its own noun (not immediately adjacent to "Intern") or because the
    # trade itself (HVAC, electrician) had no keyword at all.
    assert classify_internship("HVAC Technician Intern") is None
    assert classify_internship("Electrician Technician Intern") is None
    assert classify_internship("Military DoD SkillBridge Internship - Maintenance Technician") is None
    assert classify_internship("Supplier Industrial Engineer (Internship)") is None
    assert classify_internship("2027 Industrial Engineering Summer Intern - Chicago IL") is None
    assert classify_internship("2027 Summer Intern - Manufacturing Engineering - Body Center") is None
    assert classify_internship("Internship - CRO Manufacturing Engineer") is None
    assert classify_internship("Manufacturing Intern - Process Engineering") is None


def test_capital_markets_is_industry_scoped_to_real_estate():
    # Phase 10 Step 9: "Capital Markets" means real-estate investment
    # sales/financing at a real-estate services firm (JLL) but
    # investment-banking capital markets at a bank - a full-dataset scan
    # found both meanings recurring across unrelated companies, so the
    # keyword is scoped to Company.industry rather than added globally.
    assert classify_internship(
        "Capital Markets Summer 2027 Internship - Miami, FL", industry="Real Estate"
    ) == InternshipCategory.REAL_ESTATE
    # Without the industry context (or with a different industry, e.g. a
    # bank), the same title must NOT be swept into Real Estate.
    assert classify_internship("Capital Markets Summer 2027 Internship - Miami, FL") == InternshipCategory.OTHER
    assert classify_internship(
        "Capital Markets Off Cycle Internship Programme 2027 Frankfurt", industry="Financial Services"
    ) == InternshipCategory.OTHER
    # A bank's own "capital markets" posting must never become Real
    # Estate just because some other company shares the phrase.
    assert classify_internship(
        "Capital Markets Summer Internship Programme 2027 London", industry="Financial Services"
    ) != InternshipCategory.REAL_ESTATE
