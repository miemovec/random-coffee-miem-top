"""Add matching_rate table

Revision ID: bb2e8709b8dd
Revises: 
Create Date: 2025-01-16 22:34:57.559573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb2e8709b8dd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('all_users',
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('age', sa.Integer(), nullable=False),
    sa.Column('sex', sa.String(), nullable=False),
    sa.Column('pair_sex', sa.String(), nullable=False),
    sa.Column('specialization', sa.String(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('tags', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('chat_id'),
    sa.UniqueConstraint('chat_id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('participants',
    sa.Column('chat_id', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('chat_id'),
    sa.UniqueConstraint('chat_id')
    )
    op.create_table('matches',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_1', sa.String(), nullable=False),
    sa.Column('user_2', sa.String(), nullable=False),
    sa.Column('similarity', sa.Float(), nullable=False),
    sa.Column('matching_num', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_1'], ['all_users.chat_id'], ),
    sa.ForeignKeyConstraint(['user_2'], ['all_users.chat_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('matching_rate',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_1', sa.String(), nullable=False),
    sa.Column('user_2', sa.String(), nullable=False),
    sa.Column('matching_num', sa.Integer(), nullable=False),
    sa.Column('rating_from_user_1', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user_1'], ['all_users.chat_id'], ),
    sa.ForeignKeyConstraint(['user_2'], ['all_users.chat_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('matching_rate')
    op.drop_table('matches')
    op.drop_table('participants')
    op.drop_table('all_users')
    # ### end Alembic commands ###
