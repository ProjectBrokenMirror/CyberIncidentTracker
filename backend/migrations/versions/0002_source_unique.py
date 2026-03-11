"""Add uniqueness for incident source URLs

Revision ID: 0002_source_unique
Revises: 0001_initial_schema
Create Date: 2026-03-11
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_source_unique"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_incident_sources_source_name_source_url",
        "incident_sources",
        ["source_name", "source_url"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_incident_sources_source_name_source_url",
        "incident_sources",
        type_="unique",
    )
