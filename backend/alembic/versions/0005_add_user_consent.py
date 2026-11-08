"""add user consent columns

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-01 11:05:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: str | Sequence[str] | None = '0004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSENT_CONSISTENT = '(consent_accepted_at IS NULL) = (consent_policy_version IS NULL)'


def upgrade() -> None:
    """Upgrade schema."""
    # RF-USR-10: fecha y versión de la política aceptada. Nulas para las cuentas
    # anteriores a la política, porque no hubo aceptación que registrar.
    op.add_column(
        'users', sa.Column('consent_accepted_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'users', sa.Column('consent_policy_version', sa.String(length=20), nullable=True)
    )
    op.create_check_constraint(
        op.f('ck_users_consent_consistent'), 'users', CONSENT_CONSISTENT
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_users_consent_consistent'), 'users', type_='check')
    op.drop_column('users', 'consent_policy_version')
    op.drop_column('users', 'consent_accepted_at')
