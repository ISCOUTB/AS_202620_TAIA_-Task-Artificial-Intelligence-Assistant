"""add study plan preferences and busy blocks

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-22 10:09:47.396493

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: str | Sequence[str] | None = '0006'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# El tipo `weekday` ya existe (0002): se reutiliza sin crearlo otra vez.
WEEKDAY = postgresql.ENUM(
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    name='weekday', create_type=False,
)
BUSY_BLOCK_KIND = postgresql.ENUM('work', 'commitment', name='busy_block_kind')
STUDY_TIME_PREFERENCE = postgresql.ENUM('morning', 'afternoon', 'evening', 'any', name='study_time_preference')


def upgrade() -> None:
    """RF-EST-01: trabajo, compromisos fijos, máximo diario y momento preferido (diccionario 6.6 y 6.10)."""
    bind = op.get_bind()
    BUSY_BLOCK_KIND.create(bind, checkfirst=True)
    STUDY_TIME_PREFERENCE.create(bind, checkfirst=True)
    op.create_table('study_plan_busy_blocks',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('study_plan_id', sa.Uuid(), nullable=False),
    sa.Column('kind', postgresql.ENUM(name='busy_block_kind', create_type=False), nullable=False),
    sa.Column('weekday', WEEKDAY, nullable=False),
    sa.Column('start_time', sa.Time(), nullable=False),
    sa.Column('end_time', sa.Time(), nullable=False),
    sa.CheckConstraint('end_time > start_time', name=op.f('ck_study_plan_busy_blocks_ends_after_starts')),
    sa.ForeignKeyConstraint(['study_plan_id'], ['study_plans.id'], name=op.f('fk_study_plan_busy_blocks_study_plan_id_study_plans'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_study_plan_busy_blocks'))
    )
    op.create_index(op.f('ix_study_plan_busy_blocks_study_plan_id'), 'study_plan_busy_blocks', ['study_plan_id'], unique=False)
    op.add_column('study_plans', sa.Column('max_daily_minutes', sa.SmallInteger(), nullable=True))
    op.add_column('study_plans', sa.Column('preferred_time', postgresql.ENUM(name='study_time_preference', create_type=False), server_default='any', nullable=False))
    # Alembic no detecta CHECK nuevos en tablas existentes: se escribe a mano.
    op.create_check_constraint(
        op.f('ck_study_plans_max_daily_minutes_fits_session'),
        'study_plans',
        'max_daily_minutes IS NULL OR max_daily_minutes >= session_minutes',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_study_plans_max_daily_minutes_fits_session'), 'study_plans', type_='check')
    op.drop_column('study_plans', 'preferred_time')
    op.drop_column('study_plans', 'max_daily_minutes')
    op.drop_index(op.f('ix_study_plan_busy_blocks_study_plan_id'), table_name='study_plan_busy_blocks')
    op.drop_table('study_plan_busy_blocks')
    bind = op.get_bind()
    STUDY_TIME_PREFERENCE.drop(bind, checkfirst=True)
    BUSY_BLOCK_KIND.drop(bind, checkfirst=True)
