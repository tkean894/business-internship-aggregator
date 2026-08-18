from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.database.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for a single request, always closed after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
