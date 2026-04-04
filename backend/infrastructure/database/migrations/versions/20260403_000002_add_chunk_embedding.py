from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260403_000002"
down_revision = "20260403_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute("ALTER TABLE chunks ADD COLUMN embedding vector")
    else:
        op.add_column("chunks", sa.Column("embedding", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("chunks", "embedding")
