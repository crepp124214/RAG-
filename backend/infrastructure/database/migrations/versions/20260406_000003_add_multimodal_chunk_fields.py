"""add multimodal chunk fields

Revision ID: 20260406_000003
Revises: 20260406_000002
Create Date: 2026-04-06 00:03:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '20260406_000003'
down_revision = '20260406_000002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('chunks', sa.Column('asset_index', sa.Integer(), nullable=True))
    op.add_column('chunks', sa.Column('asset_label', sa.String(length=255), nullable=True))
    op.add_column('chunks', sa.Column('asset_path', sa.Text(), nullable=True))
    op.add_column('chunks', sa.Column('bbox', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('chunks', 'bbox')
    op.drop_column('chunks', 'asset_path')
    op.drop_column('chunks', 'asset_label')
    op.drop_column('chunks', 'asset_index')
