"""add document tags and session enhancements

Revision ID: 20260413_000005
Revises: 20260406_000004
Create Date: 2026-04-13 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '20260413_000005'
down_revision = '20260406_000004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create document_tags table
    op.create_table(
        'document_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=False, server_default='#409EFF'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_document_tags')),
        sa.UniqueConstraint('name', name=op.f('uq_document_tags_name'))
    )

    # Create document_tag_relations table
    op.create_table(
        'document_tag_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.String(length=36), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(
            ['document_id'],
            ['documents.id'],
            name=op.f('fk_document_tag_relations_document_id_documents'),
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['tag_id'],
            ['document_tags.id'],
            name=op.f('fk_document_tag_relations_tag_id_document_tags'),
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_document_tag_relations')),
        sa.UniqueConstraint('document_id', 'tag_id', name=op.f('uq_document_tag_relations_document_id_tag_id'))
    )

    # Create indexes for document_tag_relations
    op.create_index(
        op.f('ix_document_tag_relations_document_id'),
        'document_tag_relations',
        ['document_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_document_tag_relations_tag_id'),
        'document_tag_relations',
        ['tag_id'],
        unique=False
    )

    # Extend sessions table with new columns
    op.add_column('sessions', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'))

    # Create indexes for sessions
    op.create_index(
        op.f('ix_sessions_is_pinned'),
        'sessions',
        ['is_pinned'],
        unique=False
    )
    op.create_index(
        op.f('ix_sessions_updated_at'),
        'sessions',
        ['updated_at'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes for sessions
    op.drop_index(op.f('ix_sessions_updated_at'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_is_pinned'), table_name='sessions')

    # Drop columns from sessions
    op.drop_column('sessions', 'is_pinned')

    # Drop indexes for document_tag_relations
    op.drop_index(op.f('ix_document_tag_relations_tag_id'), table_name='document_tag_relations')
    op.drop_index(op.f('ix_document_tag_relations_document_id'), table_name='document_tag_relations')

    # Drop tables
    op.drop_table('document_tag_relations')
    op.drop_table('document_tags')
