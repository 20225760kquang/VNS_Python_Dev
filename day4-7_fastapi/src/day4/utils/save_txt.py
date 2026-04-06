from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Sequence

from models import Blog, Comment


def to_txt_datetime(value: datetime | None) -> str:
    return value.isoformat() if value else "null"


def save_blogs_to_txt(blogs: Sequence[Blog], output_path: str | Path) -> None:
    path = Path(output_path)
    lines = ["blog_id|title|content|created_at|status|published_at|updated_at|author_id"]

    for blog in sorted(blogs, key=lambda item: item.blog_id):
        lines.append(
            "|".join(
                [
                    str(blog.blog_id),
                    blog.title,
                    blog.content,
                    blog.created_at.isoformat(),
                    blog.status,
                    to_txt_datetime(blog.published_at),
                    to_txt_datetime(blog.updated_at),
                    str(blog.author_id),
                ]
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_comments_to_txt(comments: Sequence[Comment], output_path: str | Path) -> None:
    path = Path(output_path)
    lines = ["comment_id|user_id|blog_id|parent_id|content|created_at|updated_at"]

    for comment in sorted(comments, key=lambda item: item.comment_id):
        lines.append(
            "|".join(
                [
                    str(comment.comment_id),
                    str(comment.user_id),
                    str(comment.blog_id),
                    str(comment.parent_id) if comment.parent_id is not None else "null",
                    comment.content,
                    comment.created_at.isoformat(),
                    to_txt_datetime(comment.updated_at),
                ]
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")