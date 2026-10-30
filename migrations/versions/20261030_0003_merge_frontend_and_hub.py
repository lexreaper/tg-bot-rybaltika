"""Merge the frontend and hub migration branches; restore menu tables if needed.

Revision ID: 20261030_0003
Revises: 20261030_0002, 2a6e5b7c9012
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime, time, timezone


revision: str = "20261030_0003"
down_revision: Union[str, Sequence[str], None] = (
    "20261030_0002",
    "2a6e5b7c9012",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    offline = op.get_context().as_sql
    tables = set() if offline else set(sa.inspect(connection).get_table_names())

    metadata = sa.MetaData()
    categories = sa.Table(
        "categories",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    dishes = sa.Table(
        "dishes",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("image_url", sa.String()),
        sa.Column("is_available", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.execute(sa.schema.CreateTable(categories, if_not_exists=True))
    op.execute(sa.schema.CreateTable(dishes, if_not_exists=True))

    loyalty_columns = (
        set()
        if offline or "loyalty_info" not in tables
        else {column["name"] for column in sa.inspect(connection).get_columns("loyalty_info")}
    )
    if offline or "summary" not in loyalty_columns:
        op.add_column(
            "loyalty_info",
            sa.Column(
                "summary",
                sa.String(length=300),
                nullable=False,
                server_default=sa.text("''"),
            ),
        )
    if offline or "version" not in loyalty_columns:
        op.add_column(
            "loyalty_info",
            sa.Column(
                "version",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("1"),
            ),
        )

    if offline:
        for table_name in ("site_events", "site_vacancies", "loyalty_page"):
            op.drop_table(table_name)
        return

    metadata = sa.MetaData()
    if "site_events" in tables:
        legacy_events = sa.Table("site_events", metadata, autoload_with=connection)
        events = sa.Table("events", metadata, autoload_with=connection)
        for row in connection.execute(sa.select(legacy_events)).mappings():
            migrated_at = datetime.now(timezone.utc)
            starts_at = datetime.combine(
                row["event_date"], time.min, tzinfo=timezone.utc
            )
            connection.execute(
                events.insert().values(
                    title=row["title"],
                    description=row["description"],
                    starts_at=starts_at,
                    image_url=row["image_url"],
                    is_published=row["is_published"],
                    created_at=migrated_at,
                    updated_at=migrated_at,
                )
            )

    if "site_vacancies" in tables:
        legacy_vacancies = sa.Table(
            "site_vacancies", metadata, autoload_with=connection
        )
        vacancies = sa.Table("vacancies", metadata, autoload_with=connection)
        for row in connection.execute(sa.select(legacy_vacancies)).mappings():
            migrated_at = datetime.now(timezone.utc)
            connection.execute(
                vacancies.insert().values(
                    title=row["position"],
                    description=row["description"],
                    salary=row["salary"],
                    is_published=row["is_published"],
                    created_at=migrated_at,
                    updated_at=migrated_at,
                )
            )

    if "loyalty_page" in tables:
        legacy_loyalty = sa.Table("loyalty_page", metadata, autoload_with=connection)
        loyalty_info = sa.Table("loyalty_info", metadata, autoload_with=connection)
        existing_page = connection.execute(
            sa.select(loyalty_info.c.id).where(loyalty_info.c.key == "loyalty")
        ).first()
        if existing_page is None:
            row = connection.execute(sa.select(legacy_loyalty)).mappings().first()
            if row is not None:
                connection.execute(
                    loyalty_info.insert().values(
                        key="loyalty",
                        title=row["title"],
                        summary=row["summary"],
                        content=row["body"],
                        version=row["version"],
                        is_published=row["is_published"],
                        created_at=row["updated_at"],
                        updated_at=row["updated_at"],
                    )
                )

    for table_name in ("loyalty_page", "site_vacancies", "site_events"):
        if table_name in tables:
            op.drop_table(table_name)


def downgrade() -> None:
    if op.get_context().as_sql:
        op.drop_column("loyalty_info", "version")
        op.drop_column("loyalty_info", "summary")
        return

    if "loyalty_info" not in sa.inspect(op.get_bind()).get_table_names():
        return
    columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("loyalty_info")
    }
    if "version" in columns:
        op.drop_column("loyalty_info", "version")
    if "summary" in columns:
        op.drop_column("loyalty_info", "summary")
