"""create videos and snapshots

Revision ID: 7f41252fa94b
Revises:
Create Date: 2026-02-03 16:42:47.244557

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f41252fa94b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "videos",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("creator_id", sa.String(length=36), nullable=False),
        sa.Column("video_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("views_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("likes_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("comments_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reports_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_videos_creator_id", "videos", ["creator_id"], unique=False)
    op.create_index(
        "ix_videos_video_created_at",
        "videos",
        ["video_created_at"],
        unique=False,
    )

    op.create_table(
        "video_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("video_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("views_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("likes_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("comments_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reports_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("delta_views_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("delta_likes_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("delta_comments_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("delta_reports_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_video_snapshots_video_id", "video_snapshots", ["video_id"], unique=False)
    op.create_index(
        "ix_video_snapshots_created_at",
        "video_snapshots",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_video_snapshots_video_id_created_at",
        "video_snapshots",
        ["video_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_video_snapshots_video_id_created_at", table_name="video_snapshots")
    op.drop_index("ix_video_snapshots_created_at", table_name="video_snapshots")
    op.drop_index("ix_video_snapshots_video_id", table_name="video_snapshots")
    op.drop_table("video_snapshots")

    op.drop_index("ix_videos_video_created_at", table_name="videos")
    op.drop_index("ix_videos_creator_id", table_name="videos")
    op.drop_table("videos")
