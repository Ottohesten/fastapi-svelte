"""Add privacy-preserving hourly analytics aggregates

Revision ID: b4d9a6e3c8f2
Revises: a7c4e2f9b1d3
Create Date: 2026-07-15 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4d9a6e3c8f2"
down_revision: Union[str, None] = "a7c4e2f9b1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analytics_hourly_bucket",
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric_name", sa.String(length=40), nullable=False),
        sa.Column("route", sa.String(length=200), nullable=False),
        sa.Column("authenticated", sa.Boolean(), nullable=False),
        sa.Column(
            "event_count",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.CheckConstraint(
            "metric_name IN ('site.page_view', 'site.browser_session.started')",
            name="ck_analytics_hourly_bucket_metric_name",
        ),
        sa.CheckConstraint(
            "event_count >= 0",
            name="ck_analytics_hourly_bucket_event_count_nonnegative",
        ),
        sa.PrimaryKeyConstraint(
            "bucket_start",
            "metric_name",
            "route",
            "authenticated",
            name="pk_analytics_hourly_bucket",
        ),
    )


def downgrade() -> None:
    op.drop_table("analytics_hourly_bucket")
