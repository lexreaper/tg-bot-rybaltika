"""Drop unused booking and review data while preserving the menu.

Revision ID: 20261030_0002
Revises: 20261030_0001
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261030_0002"
down_revision: Union[str, Sequence[str], None] = "20261030_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    metadata = sa.MetaData()
    for table_name in ("reviews", "bookings", "users"):
        op.execute(
            sa.schema.DropTable(
                sa.Table(table_name, metadata),
                if_exists=True,
            )
        )


def downgrade() -> None:
    metadata = sa.MetaData()
    users = sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("username", sa.String()),
        sa.Column("first_name", sa.String()),
        sa.Column("last_name", sa.String()),
        sa.Column("phone", sa.String()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    bookings = sa.Table(
        "bookings",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("guest_count", sa.Integer(), nullable=False),
        sa.Column("booking_date", sa.Date(), nullable=False),
        sa.Column("booking_time", sa.Time(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'confirmed', 'cancelled')", name="ck_bookings_status"),
        sa.CheckConstraint("guest_count > 0", name="ck_bookings_guest_count_positive"),
    )
    reviews = sa.Table(
        "reviews",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"),
    )
    for table in (users, bookings, reviews):
        op.execute(sa.schema.CreateTable(table, if_not_exists=True))
