"""Public content sections and the editable loyalty page.

Revision ID: 2a6e5b7c9012
Revises: 70093c39af40
"""
from alembic import op
import sqlalchemy as sa

revision = '2a6e5b7c9012'
down_revision = '70093c39af40'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(160), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_table('vacancies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('position', sa.String(160), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('salary', sa.String(200), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.create_table('loyalty_page',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(120), nullable=False),
        sa.Column('summary', sa.String(300), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('id = 1', name='ck_loyalty_single_page'),
    )


def downgrade():
    op.drop_table('loyalty_page')
    op.drop_table('vacancies')
    op.drop_table('events')
