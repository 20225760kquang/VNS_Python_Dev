"""add user role column

Revision ID: 20260408_01
Revises:
Create Date: 2026-04-08 10:29:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260408_01"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("user_id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False, unique=True),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False, server_default="normal_user"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        )

    if "blogs" not in existing_tables:
        op.create_table(
            "blogs",
            sa.Column("blog_id", sa.Integer(), primary_key=True, index=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("published_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False),
        )

    if "comments" not in existing_tables:
        op.create_table(
            "comments",
            sa.Column("comment_id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False),
            sa.Column("blog_id", sa.Integer(), sa.ForeignKey("blogs.blog_id"), nullable=False),
            sa.Column("parent_id", sa.Integer(), sa.ForeignKey("comments.comment_id"), nullable=True),
            sa.Column("content", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )

    if "users" in existing_tables:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "role" not in user_columns:
            op.add_column(
                "users",
                sa.Column("role", sa.String(), nullable=False, server_default="normal_user"),
            )


def downgrade() -> None:
    op.drop_table("comments")
    op.drop_table("blogs")
    op.drop_table("users")
