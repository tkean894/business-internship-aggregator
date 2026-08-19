"""add sales category and scraper_runs table

Revision ID: dfdc769405fd
Revises: 0001_initial_schema
Create Date: 2026-08-19 00:01:19.571216

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'dfdc769405fd'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None

SCRAPER_RUN_STATUS_VALUES = ("success", "failed")


def upgrade() -> None:
    # Phase 7, Step 5: a real, recurring taxonomy gap (Braze's "Business
    # Development Representative Intern", Abbott's "Commercial Excellence
    # Intern", SpotHopper's "Business Development Internship" all fell
    # into OTHER with no better fit). ADD VALUE IF NOT EXISTS is safe to
    # run inside Alembic's transaction on Postgres 12+ as long as the new
    # value isn't also *used* in this same migration - it isn't.
    op.execute("ALTER TYPE internship_category ADD VALUE IF NOT EXISTS 'Sales'")

    # Phase 7, Step 8/9: persistent scraper-run metrics.
    bind = op.get_bind()
    postgresql.ENUM(*SCRAPER_RUN_STATUS_VALUES, name="scraper_run_status").create(bind, checkfirst=True)
    scraper_run_status = postgresql.ENUM(
        *SCRAPER_RUN_STATUS_VALUES, name="scraper_run_status", create_type=False
    )

    op.create_table(
        "scraper_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_slug", sa.String(255), nullable=False),
        sa.Column("scraper_name", sa.String(255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", scraper_run_status, nullable=False),
        sa.Column("raw_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("relevant_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deactivated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("idx_scraper_runs_company_slug", "scraper_runs", ["company_slug"])
    op.create_index("idx_scraper_runs_started_at", "scraper_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("idx_scraper_runs_started_at", table_name="scraper_runs")
    op.drop_index("idx_scraper_runs_company_slug", table_name="scraper_runs")
    op.drop_table("scraper_runs")
    postgresql.ENUM(name="scraper_run_status").drop(op.get_bind(), checkfirst=True)

    # Postgres has no ALTER TYPE ... DROP VALUE - removing an enum value
    # cleanly requires rebuilding the type (create new type, migrate
    # column, drop old type) and is deliberately not implemented here
    # since no downgrade in this project's history has ever been run
    # against real data. If this downgrade is ever needed for real,
    # verify no row uses category = 'Sales' first.