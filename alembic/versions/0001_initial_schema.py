"""initial schema: companies and internships

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

INTERNSHIP_CATEGORY_VALUES = (
    "Product Management",
    "Business Analytics",
    "Finance",
    "Accounting",
    "Consulting",
    "Marketing",
    "Operations",
    "Supply Chain",
    "Strategy",
    "Human Resources",
    "Other",
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create the enum type once, explicitly, then reference it from the
    # column below with create_type=False. Without create_type=False,
    # SQLAlchemy's create_table() would also try to CREATE TYPE for the
    # enum-typed column and fail with "type already exists".
    postgresql.ENUM(*INTERNSHIP_CATEGORY_VALUES, name="internship_category").create(
        bind, checkfirst=True
    )
    internship_category = postgresql.ENUM(
        *INTERNSHIP_CATEGORY_VALUES, name="internship_category", create_type=False
    )

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("career_url", sa.Text(), nullable=False),
        sa.Column("website_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_companies_is_active", "companies", ["is_active"])

    op.create_table(
        "internships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", internship_category, nullable=False, server_default="Other"),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=False, server_default="Internship"),
        sa.Column("application_url", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("posted_date", sa.Date(), nullable=True),
        sa.Column("application_deadline", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("dedupe_key", sa.String(64), nullable=False, unique=True),
    )
    op.create_index("idx_internships_company_id", "internships", ["company_id"])
    op.create_index("idx_internships_category", "internships", ["category"])
    op.create_index("idx_internships_is_active", "internships", ["is_active"])
    op.create_index("idx_internships_posted_date", "internships", ["posted_date"])
    op.create_index("idx_internships_source_url", "internships", ["source_url"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        "CREATE TRIGGER trg_companies_updated_at BEFORE UPDATE ON companies "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )
    op.execute(
        "CREATE TRIGGER trg_internships_updated_at BEFORE UPDATE ON internships "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_internships_updated_at ON internships;")
    op.execute("DROP TRIGGER IF EXISTS trg_companies_updated_at ON companies;")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
    op.drop_table("internships")
    op.drop_table("companies")
    postgresql.ENUM(name="internship_category").drop(op.get_bind(), checkfirst=True)
