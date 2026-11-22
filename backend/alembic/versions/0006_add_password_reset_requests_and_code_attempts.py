"""add password reset requests and code attempts

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-21 09:33:40.861593

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: str | Sequence[str] | None = '0005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FAILED_ATTEMPTS_RANGE = 'failed_attempts BETWEEN 0 AND 5'


def upgrade() -> None:
    """Upgrade schema."""
    # RNF-03 y RF-USR-08: una fila por solicitud, exista o no la cuenta (diccionario 5.7).
    op.create_table('password_reset_requests',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_password_reset_requests'))
    )
    op.create_index('ix_password_reset_requests_email_requested_at', 'password_reset_requests', ['email', 'requested_at'], unique=False)
    # RF-USR-08: el token pasa a ser un código de 6 dígitos con 5 intentos (diccionario 5.4).
    # Dos usuarios pueden recibir el mismo código, así que `token_hash` deja de ser único.
    op.add_column('password_reset_tokens', sa.Column('failed_attempts', sa.SmallInteger(), server_default=sa.text('0'), nullable=False))
    op.create_check_constraint(
        op.f('ck_password_reset_tokens_failed_attempts_range'), 'password_reset_tokens', FAILED_ATTEMPTS_RANGE
    )
    op.drop_constraint(op.f('uq_password_reset_tokens_token_hash'), 'password_reset_tokens', type_='unique')


def downgrade() -> None:
    """Downgrade schema."""
    # Los códigos de 6 dígitos pueden repetirse y no caben en la restricción única anterior.
    op.execute('DELETE FROM password_reset_tokens')
    op.create_unique_constraint(op.f('uq_password_reset_tokens_token_hash'), 'password_reset_tokens', ['token_hash'])
    op.drop_constraint(
        op.f('ck_password_reset_tokens_failed_attempts_range'), 'password_reset_tokens', type_='check'
    )
    op.drop_column('password_reset_tokens', 'failed_attempts')
    op.drop_index('ix_password_reset_requests_email_requested_at', table_name='password_reset_requests')
    op.drop_table('password_reset_requests')
