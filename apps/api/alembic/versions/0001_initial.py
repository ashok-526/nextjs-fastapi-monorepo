"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2025-09-04 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enums
    visibility_enum = postgresql.ENUM("public", "friends", "private", name="visibility")
    visibility_enum.create(op.get_bind(), checkfirst=True)

    friendship_status_enum = postgresql.ENUM(
        "pending", "accepted", "blocked", name="friendship_status"
    )
    friendship_status_enum.create(op.get_bind(), checkfirst=True)

    reaction_type_enum = postgresql.ENUM(
        "like", "love", "haha", "wow", "sad", "angry", name="reaction_type"
    )
    reaction_type_enum.create(op.get_bind(), checkfirst=True)

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )

    # profiles
    op.create_table(
        "profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("visibility", visibility_enum, server_default=sa.text("'public'"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_profiles_user_id_users"),
        sa.PrimaryKeyConstraint("user_id", name="pk_profiles"),
    )

    # friendships
    op.create_table(
        "friendships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("requester_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("addressee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", friendship_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE", name="fk_friendships_requester_id_users"),
        sa.ForeignKeyConstraint(["addressee_id"], ["users.id"], ondelete="CASCADE", name="fk_friendships_addressee_id_users"),
        sa.UniqueConstraint("requester_id", "addressee_id", name="uq_friendships_requester_addressee"),
    )

    # blocks
    op.create_table(
        "blocks",
        sa.Column("blocker_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("blocked_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["blocker_id"], ["users.id"], ondelete="CASCADE", name="fk_blocks_blocker_id_users"),
        sa.ForeignKeyConstraint(["blocked_id"], ["users.id"], ondelete="CASCADE", name="fk_blocks_blocked_id_users"),
        sa.PrimaryKeyConstraint("blocker_id", "blocked_id", name="pk_blocks"),
    )

    # posts
    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("media_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("visibility", visibility_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE", name="fk_posts_author_id_users"),
    )

    # comments
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_comment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE", name="fk_comments_post_id_posts"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE", name="fk_comments_author_id_users"),
        sa.ForeignKeyConstraint(["parent_comment_id"], ["comments.id"], ondelete="SET NULL", name="fk_comments_parent_comment_id_comments"),
    )

    # reactions
    op.create_table(
        "reactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", reaction_type_enum, nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE", name="fk_reactions_post_id_posts"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_reactions_user_id_users"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_reactions_post_user"),
    )

    # notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_notifications_user_id_users"),
    )

    # Indexes
    op.create_index("ix_comments_post_created", "comments", ["post_id", "created_at"], unique=False)
    op.create_index("ix_friendships_addressee_status", "friendships", ["addressee_id", "status"], unique=False)
    op.create_index("ix_reactions_post", "reactions", ["post_id"], unique=False)

    # Desc indexes with raw SQL for DESC
    op.execute("CREATE INDEX ix_posts_author_created_desc ON posts (author_id, created_at DESC)")
    op.execute(
        "CREATE INDEX ix_notifications_user_isread_created_desc ON notifications (user_id, is_read, created_at DESC)"
    )


def downgrade() -> None:
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS ix_notifications_user_isread_created_desc")
    op.execute("DROP INDEX IF EXISTS ix_posts_author_created_desc")
    op.drop_index("ix_reactions_post", table_name="reactions")
    op.drop_index("ix_friendships_addressee_status", table_name="friendships")
    op.drop_index("ix_comments_post_created", table_name="comments")

    # Drop tables in reverse order
    op.drop_table("notifications")
    op.drop_table("reactions")
    op.drop_table("comments")
    op.drop_table("posts")
    op.drop_table("blocks")
    op.drop_table("friendships")
    op.drop_table("profiles")
    op.drop_table("users")

    # Drop enums
    postgresql.ENUM(name="reaction_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="friendship_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="visibility").drop(op.get_bind(), checkfirst=True)

