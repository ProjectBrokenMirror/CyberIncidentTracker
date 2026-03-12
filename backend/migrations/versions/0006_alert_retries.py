"""Add retry metadata for notification events

Revision ID: 0006_alert_retries
Revises: 0005_alerting
Create Date: 2026-03-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_alert_retries"
down_revision = "0005_alerting"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notification_events", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("notification_events", sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notification_events", sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_notification_events_status", "notification_events", ["status"], unique=False)
    op.create_index("ix_notification_events_next_retry_at", "notification_events", ["next_retry_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notification_events_next_retry_at", table_name="notification_events")
    op.drop_index("ix_notification_events_status", table_name="notification_events")
    op.drop_column("notification_events", "next_retry_at")
    op.drop_column("notification_events", "last_attempt_at")
    op.drop_column("notification_events", "attempt_count")
