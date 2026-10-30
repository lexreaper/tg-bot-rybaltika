"""Add content tables for the Manufaktura network hub.

Revision ID: 20261030_0001
Revises: 70093c39af40
Create Date: 2026-10-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261030_0001"
down_revision: Union[str, Sequence[str], None] = "70093c39af40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    if not op.get_context().as_sql:
        tables = set(sa.inspect(connection).get_table_names())
        for source_name, target_name, columns in (
            (
                "events",
                "site_events",
                ("title", "description", "event_date", "image_url", "is_published"),
            ),
            (
                "vacancies",
                "site_vacancies",
                ("position", "description", "salary", "is_published"),
            ),
        ):
            if source_name not in tables:
                continue
            source_columns = {
                column["name"]
                for column in sa.inspect(connection).get_columns(source_name)
            }
            is_hub_table = (
                "starts_at" in source_columns
                if source_name == "events"
                else "title" in source_columns
            )
            if is_hub_table:
                continue
            if target_name not in tables:
                op.rename_table(source_name, target_name)
                tables.remove(source_name)
                tables.add(target_name)
                continue

            source = sa.Table(source_name, sa.MetaData(), autoload_with=connection)
            target = sa.Table(target_name, sa.MetaData(), autoload_with=connection)
            required_columns = set(columns)
            if not required_columns <= source_columns:
                raise RuntimeError(
                    f"Cannot migrate legacy {source_name}: missing columns "
                    f"{sorted(required_columns - source_columns)}."
                )
            target_columns = set(target.c.keys())
            if not required_columns <= target_columns:
                raise RuntimeError(
                    f"Cannot merge {source_name} into {target_name}: "
                    "the destination has an unexpected schema."
                )
            for row in connection.execute(sa.select(source)).mappings():
                connection.execute(
                    target.insert().values(
                        {name: row[name] for name in columns}
                    )
                )
            op.drop_table(source_name)
            tables.remove(source_name)

    op.create_table(
        "bars",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("website_url", sa.String(length=2048), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=2048), nullable=True),
        sa.Column(
            "is_published",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=            sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=            sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bar_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column(
            "is_published",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=            sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=            sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "ends_at IS NULL OR ends_at > starts_at",
            name="ck_events_ends_after_start",
        ),
        sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_bar_id", "events", ["bar_id"])
    op.create_index("ix_events_starts_at", "events", ["starts_at"])
    op.create_table(
        "vacancies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bar_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("employment_type", sa.String(length=100), nullable=True),
        sa.Column("salary", sa.String(length=200), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column(
            "is_published",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=            sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=            sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vacancies_bar_id", "vacancies", ["bar_id"])
    op.create_table(
        "loyalty_info",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("terms_url", sa.String(length=2048), nullable=True),
        sa.Column(
            "is_published",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=            sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=            sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_loyalty_info_key"),
    )


def downgrade() -> None:
    op.drop_table("loyalty_info")
    op.drop_index("ix_vacancies_bar_id", table_name="vacancies")
    op.drop_table("vacancies")
    op.drop_index("ix_events_starts_at", table_name="events")
    op.drop_index("ix_events_bar_id", table_name="events")
    op.drop_table("events")
    op.drop_table("bars")
