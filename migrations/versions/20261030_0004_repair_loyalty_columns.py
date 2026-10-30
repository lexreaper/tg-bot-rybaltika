"""Ensure loyalty summary and version columns exist.

Revision ID: 20261030_0004
Revises: 20261030_0003
"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "20261030_0004"
down_revision: Union[str, Sequence[str], None] = "20261030_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        return

    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if "loyalty_info" not in inspector.get_table_names():
        raise RuntimeError(
            "Cannot repair loyalty_info columns: the loyalty_info table is missing."
        )

    columns = {column["name"] for column in inspector.get_columns("loyalty_info")}
    if "summary" not in columns:
        op.add_column(
            "loyalty_info",
            sa.Column(
                "summary",
                sa.String(length=300),
                nullable=False,
                server_default=sa.text("''"),
            ),
        )
    if "version" not in columns:
        op.add_column(
            "loyalty_info",
            sa.Column(
                "version",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("1"),
            ),
        )


def downgrade() -> None:
    if context.is_offline_mode():
        return

    connection = op.get_bind()
    if "loyalty_info" not in sa.inspect(connection).get_table_names():
        return

    columns = {column["name"] for column in sa.inspect(connection).get_columns("loyalty_info")}
    if "version" in columns:
        op.drop_column("loyalty_info", "version")
    if "summary" in columns:
        op.drop_column("loyalty_info", "summary")
