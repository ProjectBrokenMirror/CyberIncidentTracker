"""Initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_organizations_canonical_name", "organizations", ["canonical_name"])
    op.create_index("ix_organizations_domain", "organizations", ["domain"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("incident_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="new"),
        sa.Column("severity", sa.String(length=30), nullable=False, server_default="medium"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.6"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_incidents_org_id", "incidents", ["org_id"])

    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("criticality", sa.String(length=50), nullable=False, server_default="medium"),
    )
    op.create_index("ix_vendors_organization_id", "vendors", ["organization_id"])

    op.create_table(
        "incident_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id"), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_incident_sources_incident_id", "incident_sources", ["incident_id"])


def downgrade() -> None:
    op.drop_index("ix_incident_sources_incident_id", table_name="incident_sources")
    op.drop_table("incident_sources")
    op.drop_index("ix_vendors_organization_id", table_name="vendors")
    op.drop_table("vendors")
    op.drop_index("ix_incidents_org_id", table_name="incidents")
    op.drop_table("incidents")
    op.drop_index("ix_organizations_domain", table_name="organizations")
    op.drop_index("ix_organizations_canonical_name", table_name="organizations")
    op.drop_table("organizations")
