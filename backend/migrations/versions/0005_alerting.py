"""Add vendor watchers and notification events

Revision ID: 0005_alerting
Revises: 0004_vendor_tenant
Create Date: 2026-03-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_alerting"
down_revision = "0004_vendor_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendor_watchers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="default"),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("vendor_id", "email", name="uq_vendor_watchers_vendor_email"),
    )
    op.create_index("ix_vendor_watchers_vendor_id", "vendor_watchers", ["vendor_id"], unique=False)
    op.create_index("ix_vendor_watchers_tenant_id", "vendor_watchers", ["tenant_id"], unique=False)

    op.create_table(
        "notification_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="default"),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("recipient_email", sa.String(length=320), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notification_events_vendor_id", "notification_events", ["vendor_id"], unique=False)
    op.create_index("ix_notification_events_incident_id", "notification_events", ["incident_id"], unique=False)
    op.create_index("ix_notification_events_tenant_id", "notification_events", ["tenant_id"], unique=False)

    op.add_column("ingestion_runs", sa.Column("total_alerts_attempted", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("ingestion_runs", sa.Column("total_alerts_sent", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("ingestion_runs", sa.Column("total_alerts_failed", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("ingestion_runs", "total_alerts_failed")
    op.drop_column("ingestion_runs", "total_alerts_sent")
    op.drop_column("ingestion_runs", "total_alerts_attempted")

    op.drop_index("ix_notification_events_tenant_id", table_name="notification_events")
    op.drop_index("ix_notification_events_incident_id", table_name="notification_events")
    op.drop_index("ix_notification_events_vendor_id", table_name="notification_events")
    op.drop_table("notification_events")

    op.drop_index("ix_vendor_watchers_tenant_id", table_name="vendor_watchers")
    op.drop_index("ix_vendor_watchers_vendor_id", table_name="vendor_watchers")
    op.drop_table("vendor_watchers")
