"""Add tenant scope to vendors

Revision ID: 0004_vendor_tenant
Revises: 0003_ingestion_runs
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_vendor_tenant"
down_revision = "0003_ingestion_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vendors", sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="default"))
    op.create_index("ix_vendors_tenant_id", "vendors", ["tenant_id"], unique=False)
    op.create_unique_constraint("uq_vendors_tenant_org", "vendors", ["tenant_id", "organization_id"])


def downgrade() -> None:
    op.drop_constraint("uq_vendors_tenant_org", "vendors", type_="unique")
    op.drop_index("ix_vendors_tenant_id", table_name="vendors")
    op.drop_column("vendors", "tenant_id")
