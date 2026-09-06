"""add legal category

Revision ID: f3a1c9d5e7b2
Revises: ae99487d261d
Create Date: 2026-09-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a1c9d5e7b2'
down_revision = 'ae99487d261d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Phase 10, Step 9: ~10 recurring active postings across 9 unrelated
    # companies (Deutsche Bank, Kraft Heinz, AIA, P&G, PwC, Federal Reserve
    # Bank of NY, Prudential, Mondelez, Cigna) justify a dedicated category -
    # see scrapers/classification.py and InternshipCategory.LEGAL.
    op.execute("ALTER TYPE internship_category ADD VALUE IF NOT EXISTS 'Legal'")


def downgrade() -> None:
    # See the Phase 7 migration's downgrade() for why removing an enum
    # value is deliberately not implemented (Postgres has no ALTER TYPE
    # ... DROP VALUE without a full type rebuild).
    pass
