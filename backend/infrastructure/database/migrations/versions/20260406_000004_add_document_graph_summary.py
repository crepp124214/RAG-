"""add document graph summary

Revision ID: 20260406_000004
Revises: 20260406_000003
Create Date: 2026-04-06 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '20260406_000004'
down_revision = '20260406_000003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('graph_status', sa.String(length=32), nullable=False, server_default='NOT_STARTED'))
    op.add_column('documents', sa.Column('graph_relation_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('documents', 'graph_relation_count')
    op.drop_column('documents', 'graph_status')
