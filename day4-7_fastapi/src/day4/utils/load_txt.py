from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
from pprint import pprint

try:
	from models import Blog, Comment, User
except ModuleNotFoundError:
	project_root = Path(__file__).resolve().parents[1]
	if str(project_root) not in sys.path:
		sys.path.insert(0, str(project_root))
	from models import Blog, Comment, User


def _parse_nullable_datetime(value: str) -> Optional[datetime]:
	raw = value.strip()
	if raw.lower() in {"", "null", "none"}:
		return None
	return datetime.fromisoformat(raw)


def _parse_nullable_int(value: str) -> Optional[int]:
	raw = value.strip()
	if raw.lower() in {"", "null", "none"}:
		return None
	return int(raw)


def _read_data_lines(file_path: Path) -> List[str]:
	if not file_path.exists():
		raise FileNotFoundError(f"Mock data file not found: {file_path}")

	lines = file_path.read_text(encoding="utf-8").splitlines()
	# Skip header row and empty lines.
	return [line for line in lines[1:] if line.strip()]


def _parse_users(file_path: Path) -> Tuple[List[User], Dict[int, User]]:
	users: List[User] = []
	users_by_id: Dict[int, User] = {}

	for line in _read_data_lines(file_path):
		user_id, name, email, hashed_password, created_at = line.split("|", 4)

		user = User(
			user_id=int(user_id),
			name=name,
			email=email,
			hashed_password=hashed_password,
			created_at=datetime.fromisoformat(created_at),
		)
		users.append(user)
		users_by_id[user.user_id] = user

	return users, users_by_id


def _parse_blogs(file_path: Path, users_by_id: Dict[int, User]) -> Tuple[List[Blog], Dict[int, Blog]]:
	blogs: List[Blog] = []
	blogs_by_id: Dict[int, Blog] = {}

	for line in _read_data_lines(file_path):
		(
			blog_id,
			title,
			content,
			created_at,
			status,
			published_at,
			updated_at,
			author_id,
		) = line.split("|", 7)

		blog = Blog(
			blog_id=int(blog_id),
			title=title,
			content=content,
			created_at=datetime.fromisoformat(created_at),
			status=status,
			published_at=_parse_nullable_datetime(published_at),
			updated_at=_parse_nullable_datetime(updated_at),
			author_id=int(author_id),
		)

		owner = users_by_id.get(blog.author_id)
		if owner is not None:
			blog.owner = owner

		blogs.append(blog)
		blogs_by_id[blog.blog_id] = blog

	return blogs, blogs_by_id


def _parse_comments(
	file_path: Path,
	users_by_id: Dict[int, User],
	blogs_by_id: Dict[int, Blog],
) -> Tuple[List[Comment], Dict[int, Comment]]:
	comments: List[Comment] = []
	comments_by_id: Dict[int, Comment] = {}

	for line in _read_data_lines(file_path):
		(
			comment_id,
			user_id,
			blog_id,
			parent_id,
			content,
			created_at,
			updated_at,
		) = line.split("|", 6)

		comment = Comment(
			comment_id=int(comment_id),
			user_id=int(user_id),
			blog_id=int(blog_id),
			parent_id=_parse_nullable_int(parent_id),
			content=content,
			created_at=datetime.fromisoformat(created_at),
			updated_at=_parse_nullable_datetime(updated_at),
		)

		user = users_by_id.get(comment.user_id)
		if user is not None:
			comment.user = user

		blog = blogs_by_id.get(comment.blog_id)
		if blog is not None:
			comment.blog = blog

		comments.append(comment)
		comments_by_id[comment.comment_id] = comment

	# Build self-referential relation after all comments are created.
	for comment in comments:
		if comment.parent_id is None:
			continue
		parent = comments_by_id.get(comment.parent_id)
		if parent is not None:
			comment.parent = parent

	return comments, comments_by_id


def load_mock_data(
	mock_data_dir: Optional[str] = None,
) -> Dict[str, object]:
	"""Load txt mock data and return in-memory ORM objects.

	Returned keys:
	- users: List[User]
	- blogs: List[Blog]
	- comments: List[Comment]
	- users_by_id: Dict[int, User]
	- blogs_by_id: Dict[int, Blog]
	- comments_by_id: Dict[int, Comment]
	"""

	base_dir = Path(mock_data_dir) if mock_data_dir else Path(__file__).resolve().parents[1] / "mock_data"

	users, users_by_id = _parse_users(base_dir / "account.txt")
	blogs, blogs_by_id = _parse_blogs(base_dir / "blogs.txt", users_by_id)
	comments, comments_by_id = _parse_comments(base_dir / "comments.txt", users_by_id, blogs_by_id)

	return {
		"users": users,
		"blogs": blogs,
		"comments": comments,
		"users_by_id": users_by_id,
		"blogs_by_id": blogs_by_id,
		"comments_by_id": comments_by_id,
	}

if __name__ == "__main__":
	default_data_path = Path(__file__).resolve().parents[1] / "mock_data"
	loaded = load_mock_data(mock_data_dir=str(default_data_path))
	print(
		f"Loaded users={len(loaded['users'])}, "
		f"blogs={len(loaded['blogs'])}, comments={len(loaded['comments'])}"
	)
	pprint(loaded)