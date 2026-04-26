"""refactor auth: add password, is_active, remove phone and name

Revision ID: b7c228b8ae3b
Revises: 8c1a2b3c4d5e
Create Date: 2026-04-26 12:50:19.022076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c228b8ae3b'
down_revision: Union[str, Sequence[str], None] = '8c1a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema. SQLite cannot ALTER COLUMN, so we drop and recreate users, products, votes."""
    op.drop_index(op.f('ix_products_created_at'), table_name='products')
    op.drop_index(op.f('ix_products_maker_id'), table_name='products')
    op.drop_table('products')
    op.drop_index(op.f('ix_votes_product_id'), table_name='votes')
    op.drop_table('votes')
    
    op.drop_table('users')
    
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username', name=op.f('uq_users_username')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email')),
    )
    
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=200), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('tagline', sa.String(length=120), nullable=False),
        sa.Column('description', sa.String(length=2000), nullable=False),
        sa.Column('website_url', sa.String(length=2000), nullable=False),
        sa.Column('logo_url', sa.String(length=2000), nullable=True),
        sa.Column('maker_id', sa.Integer(), nullable=False),
        sa.Column('vote_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['maker_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name=op.f('uq_products_slug'))
    )
    op.create_index(op.f('ix_products_maker_id'), 'products', ['maker_id'], unique=False)
    op.create_index(op.f('ix_products_created_at'), 'products', ['created_at'], unique=False)
    
    op.create_table('votes',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'product_id')
    )
    op.create_index(op.f('ix_votes_product_id'), 'votes', ['product_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema. Recreate old users table."""
    op.drop_table('users')
    
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name=op.f('uq_users_email')),
        sa.UniqueConstraint('phone', name=op.f('uq_users_phone')),
    )
    
    op.create_table('products',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('slug', sa.VARCHAR(length=200), nullable=False),
        sa.Column('name', sa.VARCHAR(length=80), nullable=False),
        sa.Column('tagline', sa.VARCHAR(length=120), nullable=False),
        sa.Column('description', sa.VARCHAR(length=2000), nullable=False),
        sa.Column('website_url', sa.VARCHAR(length=2000), nullable=False),
        sa.Column('logo_url', sa.VARCHAR(length=2000), nullable=True),
        sa.Column('maker_id', sa.INTEGER(), nullable=False),
        sa.Column('vote_count', sa.INTEGER(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DATETIME(), nullable=False),
        sa.ForeignKeyConstraint(['maker_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name=op.f('uq_products_slug'))
    )
    op.create_index(op.f('ix_products_maker_id'), 'products', ['maker_id'], unique=False)
    op.create_index(op.f('ix_products_created_at'), 'products', ['created_at'], unique=False)
    
    op.create_table('votes',
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.Column('product_id', sa.INTEGER(), nullable=False),
        sa.Column('created_at', sa.DATETIME(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'product_id')
    )
    op.create_index(op.f('ix_votes_product_id'), 'votes', ['product_id'], unique=False)
