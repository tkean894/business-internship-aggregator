"""add real estate category and company industry field

Revision ID: dda83df7adaa
Revises: dfdc769405fd
Create Date: 2026-08-19 00:40:02.005993

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dda83df7adaa'
down_revision = 'dfdc769405fd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Phase 8, Step 6: Invesco's recurring "Real Estate (Equity & Credit)"
    # postings justify a dedicated category (see scrapers/classification.py).
    op.execute("ALTER TYPE internship_category ADD VALUE IF NOT EXISTS 'Real Estate'")

    # Phase 8, Step 5: company industry metadata, to support industry
    # filtering/display. Nullable - backfilled by scrapers on their next
    # run (BaseScraper._get_or_create_company), not by this migration.
    op.add_column("companies", sa.Column("industry", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "industry")
    # See the Phase 7 migration's downgrade() for why removing an enum
    # value is deliberately not implemented (Postgres has no ALTER TYPE
    # ... DROP VALUE without a full type rebuild).
