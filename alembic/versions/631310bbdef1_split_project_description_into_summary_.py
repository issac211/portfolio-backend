"""split project description into summary and content

Revision ID: 631310bbdef1
Revises: d086cbd3eed6
Create Date: 2026-10-04 22:17:58.203326

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "631310bbdef1"
down_revision: str | Sequence[str] | None = "d086cbd3eed6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add summary as nullable
    op.add_column(
        "projects", sa.Column("summary", sa.String(length=300), nullable=True)
    )
    # 2. Backfill summary from existing description (truncated to 300 chars if necessary)
    op.execute("UPDATE projects SET summary = LEFT(description, 300)")
    # 3. Add content as nullable Text
    op.add_column("projects", sa.Column("content", sa.Text(), nullable=True))
    # 4. Enforce NOT NULL on summary now that all rows are populated
    op.alter_column("projects", "summary", nullable=False)
    # 5. Drop deprecated description column
    op.drop_column("projects", "description")


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Re-add description as nullable
    op.add_column("projects", sa.Column("description", sa.Text(), nullable=True))
    # 2. Backfill description from summary
    op.execute("UPDATE projects SET description = summary")
    # 3. Enforce NOT NULL on description
    op.alter_column("projects", "description", nullable=False)
    # 4. Drop content column
    op.drop_column("projects", "content")
    # 5. Drop summary column
    op.drop_column("projects", "summary")
