"""Add ingestion run history table

Revision ID: 0003_ingestion_runs
Revises: 0002_source_unique
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_ingestion_runs"
down_revision = "0002_source_unique"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="success"),
        sa.Column("total_raw", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_normalized", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_deduped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_persisted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_unmatched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_skipped_duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_organizations_created", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("ingestion_runs")
