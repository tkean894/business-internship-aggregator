from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and configure it."
    )

# pool_size/max_overflow explicitly sized for scrapers/scheduler.py's
# parallel run (Phase 10 Step 5 follow-up): MAX_PARALLEL_SCRAPERS=8
# concurrently-running scrapers each hold at most one connection at a
# time (their own short-lived SessionLocal(), opened and closed within
# that one company's BaseScraper.run()), so pool_size=10 already covers
# them with a couple to spare for the API server's own request handling
# in the same process where relevant; max_overflow=10 is headroom, not
# an expected steady-state number. Comfortably under typical free-tier
# Postgres connection limits (Neon/Render).
engine = create_engine(DATABASE_URL, future=True, pool_size=10, max_overflow=10)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Session:
    """Return a new SQLAlchemy session. Caller is responsible for closing it."""
    return SessionLocal()
