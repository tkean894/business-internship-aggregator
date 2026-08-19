"""add users, saved internships, notification preferences and events

Revision ID: ae99487d261d
Revises: dda83df7adaa
Create Date: 2026-08-19 02:10:36.534467

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'ae99487d261d'
down_revision = 'dda83df7adaa'
branch_labels = None
depends_on = None

NOTIFICATION_FREQUENCY_VALUES = ("immediate", "daily", "weekly", "off")
NOTIFICATION_EVENT_TYPE_VALUES = ("new_match", "saved_internship_inactive")
NOTIFICATION_EVENT_STATUS_VALUES = ("pending", "sent", "failed")


def upgrade() -> None:
    bind = op.get_bind()

    # ---------------------------------------------------------------
    # users - credentials live entirely in Clerk; this table only
    # stores the provider's user ID plus app-specific fields.
    # ---------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clerk_user_id", sa.String(255), nullable=False, unique=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ---------------------------------------------------------------
    # saved_internships
    # ---------------------------------------------------------------
    op.create_table(
        "saved_internships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("internship_id", sa.Integer(), sa.ForeignKey("internships.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "internship_id", name="uq_saved_internships_user_internship"),
    )
    op.create_index("idx_saved_internships_user_id", "saved_internships", ["user_id"])
    op.create_index("idx_saved_internships_internship_id", "saved_internships", ["internship_id"])

    # ---------------------------------------------------------------
    # notification_preferences
    # ---------------------------------------------------------------
    postgresql.ENUM(*NOTIFICATION_FREQUENCY_VALUES, name="notification_frequency").create(bind, checkfirst=True)
    notification_frequency = postgresql.ENUM(
        *NOTIFICATION_FREQUENCY_VALUES, name="notification_frequency", create_type=False
    )

    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("frequency", notification_frequency, nullable=False, server_default="off"),
        sa.Column("categories", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("industries", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("locations", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ---------------------------------------------------------------
    # notification_events - the idempotency mechanism: the unique
    # constraint below is what actually prevents a re-run of the
    # scraper/notification workflow from generating a duplicate.
    # ---------------------------------------------------------------
    postgresql.ENUM(*NOTIFICATION_EVENT_TYPE_VALUES, name="notification_event_type").create(bind, checkfirst=True)
    notification_event_type = postgresql.ENUM(
        *NOTIFICATION_EVENT_TYPE_VALUES, name="notification_event_type", create_type=False
    )
    postgresql.ENUM(*NOTIFICATION_EVENT_STATUS_VALUES, name="notification_event_status").create(bind, checkfirst=True)
    notification_event_status = postgresql.ENUM(
        *NOTIFICATION_EVENT_STATUS_VALUES, name="notification_event_status", create_type=False
    )

    op.create_table(
        "notification_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("internship_id", sa.Integer(), sa.ForeignKey("internships.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", notification_event_type, nullable=False),
        sa.Column("status", notification_event_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "user_id", "internship_id", "event_type", name="uq_notification_events_user_internship_type"
        ),
    )
    op.create_index("idx_notification_events_user_id", "notification_events", ["user_id"])
    op.create_index("idx_notification_events_status", "notification_events", ["status"])


def downgrade() -> None:
    op.drop_index("idx_notification_events_status", table_name="notification_events")
    op.drop_index("idx_notification_events_user_id", table_name="notification_events")
    op.drop_table("notification_events")
    postgresql.ENUM(name="notification_event_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="notification_event_type").drop(op.get_bind(), checkfirst=True)

    op.drop_table("notification_preferences")
    postgresql.ENUM(name="notification_frequency").drop(op.get_bind(), checkfirst=True)

    op.drop_index("idx_saved_internships_internship_id", table_name="saved_internships")
    op.drop_index("idx_saved_internships_user_id", table_name="saved_internships")
    op.drop_table("saved_internships")

    op.drop_table("users")
