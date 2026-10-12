"""rename tech_stack_csv to tags_csv

Revision ID: af22ec542233
Revises: 631310bbdef1
Create Date: 2026-10-04 22:53:06.960384

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "af22ec542233"
down_revision: str | Sequence[str] | None = "631310bbdef1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("projects", "tech_stack_csv", new_column_name="tags_csv")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("projects", "tags_csv", new_column_name="tech_stack_csv")
