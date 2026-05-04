"""add products and votes

Revision ID: 8c1a2b3c4d5e
Revises: 34d2b1704f2b
Create Date: 2026-04-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c1a2b3c4d5e"
down_revision: Union[str, Sequence[str], None] = "34d2b1704f2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("tagline", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column("website_url", sa.String(length=2000), nullable=False),
        sa.Column("logo_url", sa.String(length=2000), nullable=True),
        sa.Column("maker_id", sa.Integer(), nullable=False),
        sa.Column("vote_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["maker_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_products_slug"),
    )
    op.create_index("ix_products_created_at", "products", ["created_at"], unique=False)
    op.create_index("ix_products_maker_id", "products", ["maker_id"], unique=False)

    op.create_table(
        "votes",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "product_id"),
    )
    op.create_index("ix_votes_product_id", "votes", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_votes_product_id", table_name="votes")
    op.drop_table("votes")
    op.drop_index("ix_products_maker_id", table_name="products")
    op.drop_index("ix_products_created_at", table_name="products")
    op.drop_table("products")
