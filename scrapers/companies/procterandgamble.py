from __future__ import annotations

import logging

from scrapers.workday import WorkdayScraper


class ProcterAndGambleScraper(WorkdayScraper):
    """Procter & Gamble's public Workday job board (Phase 10 Step 5).

    Live-verified: tenant "pg", site "1000" (the numeric site path found
    via a real posting URL, not guessed). `workerSubType` facet has a
    clean "Intern/Co-Op (Fixed Term) (Trainee)" value (176 open postings
    at verification time, out of 744 total on the board) - a genuinely
    global tenant covering all P&G markets, so this scrapes worldwide
    and relies on the existing frontend US/Canada display filter to
    surface the relevant subset, the same pattern already used for
    Barclays/Disney/Airbus.
    """

    base_url = "https://pg.wd5.myworkdayjobs.com"
    tenant = "pg"
    site = "1000"
    intern_facet_id = "e294e7e48559015579693cb03207ff2b"  # "Intern/Co-Op (Fixed Term) (Trainee)"

    company_slug = "procter-and-gamble"
    company_name = "Procter & Gamble"
    career_url = "https://pg.wd5.myworkdayjobs.com/1000"
    website_url = "https://www.pg.com"
    industry = "Consumer Goods"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_result = ProcterAndGambleScraper().run()
    print(run_result.summary())
