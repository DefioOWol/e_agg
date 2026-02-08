"""empty migration

Revision ID: 78df416b6e3e
Revises:
Create Date: 2026-02-08 11:41:35.487540

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "78df416b6e3e"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
