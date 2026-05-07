"""add user_consents table

Revision ID: b1c2d3e4f5a6
Revises: 455af65ad8db
Create Date: 2026-05-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = '455af65ad8db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_consents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('agreed', sa.Boolean(), nullable=False),
        sa.Column('agreed_at', sa.DateTime(), nullable=True),
        sa.Column('declined_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id'),
    )
    op.create_index(op.f('ix_user_consents_id'), 'user_consents', ['id'], unique=False)
    op.create_index(op.f('ix_user_consents_telegram_id'), 'user_consents', ['telegram_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_consents_telegram_id'), table_name='user_consents')
    op.drop_index(op.f('ix_user_consents_id'), table_name='user_consents')
    op.drop_table('user_consents')
