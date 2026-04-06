from datetime import datetime
from pathlib import Path
from typing import List, Set

from fastapi import APIRouter, HTTPException, Query

from models import Blog, Comment
from schemas import BlogCommentListResponse, CommentCreate, CommentResponse, CommentUpdate
from utils.load_txt import load_mock_data
from utils.save_txt import save_comments_to_txt


router = APIRouter()

CURRENT_USER_ID = 1

default_data_path = Path(__file__).resolve().parents[1] / "mock_data"
comment_path = default_data_path / "comments.txt"

db_blogs: List[Blog] = []
db_comments: List[Comment] = []


def refresh_mock_state() -> None:
	global db_blogs, db_comments
	loaded = load_mock_data(mock_data_dir=str(default_data_path))
	db_blogs = loaded["blogs"]
	db_comments = loaded["comments"]


def find_blog(blog_id: int) -> Blog:
	refresh_mock_state()
	blog = next((item for item in db_blogs if item.blog_id == blog_id), None)
	if blog is None:
		raise HTTPException(status_code=404, detail="Blog not found")
	return blog


def find_comment(comment_id: int) -> Comment:
	refresh_mock_state()
	comment = next((item for item in db_comments if item.comment_id == comment_id), None)
	if comment is None:
		raise HTTPException(status_code=404, detail="Comment not found")
	return comment


def check_blog_visible(blog: Blog) -> None:
	if blog.author_id != CURRENT_USER_ID and blog.status != "published":
		raise HTTPException(status_code=403, detail="You cannot access comments of this draft blog")


def collect_comment_descendants(parent_comment_id: int) -> Set[int]:
	refresh_mock_state()
	children_map: dict[int, List[int]] = {}
	for comment in db_comments:
		if comment.parent_id is None:
			continue
		children_map.setdefault(comment.parent_id, []).append(comment.comment_id)

	to_delete: Set[int] = set()
	stack = [parent_comment_id]
	while stack:
		current = stack.pop()
		if current in to_delete:
			continue
		to_delete.add(current)
		stack.extend(children_map.get(current, []))

	return to_delete


# 1. Comment a blog or reply a comment
@router.post("/blogs/{blog_id}/comments", response_model=CommentResponse)
def create_comment(blog_id: int, request: CommentCreate) -> Comment:
	blog = find_blog(blog_id)
	check_blog_visible(blog)

	parent_id = request.parent_id
	if parent_id is not None:
		parent = find_comment(parent_id)
		if parent.blog_id != blog_id:
			raise HTTPException(status_code=400, detail="parent_id must belong to the same blog")

	next_comment_id = max((comment.comment_id for comment in db_comments), default=0) + 1
	new_comment = Comment(
		comment_id=next_comment_id,
		user_id=CURRENT_USER_ID,
		blog_id=blog_id,
		parent_id=parent_id,
		content=request.content,
		created_at=datetime.now(),
		updated_at=None,
	)

	db_comments.append(new_comment)
	save_comments_to_txt(db_comments, comment_path)
	return new_comment


# 2. Get comments of one blog
@router.get("/blogs/{blog_id}/comments", response_model=BlogCommentListResponse)
def get_blog_comments(
	blog_id: int,
	page: int = Query(1, ge=1),
	limit: int = Query(10, ge=1, le=100),
) -> BlogCommentListResponse:
	refresh_mock_state()
	blog = find_blog(blog_id)
	check_blog_visible(blog)

	comments = [comment for comment in db_comments if comment.blog_id == blog_id]
	comments = sorted(comments, key=lambda item: item.comment_id)

	total = len(comments)
	start = (page - 1) * limit
	end = start + limit

	return BlogCommentListResponse(data=comments[start:end], page=page, limit=limit, total=total)


# 3. Get one comment
@router.get("/comments/{comment_id}", response_model=CommentResponse)
def get_comment(comment_id: int) -> Comment:
	comment = find_comment(comment_id)
	blog = find_blog(comment.blog_id)
	check_blog_visible(blog)
	return comment


# 4. Update one comment
@router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(comment_id: int, request: CommentUpdate) -> Comment:
	refresh_mock_state()
	comment = find_comment(comment_id)

	if comment.user_id != CURRENT_USER_ID:
		raise HTTPException(status_code=403, detail="You can only update your own comment")

	comment.content = request.content
	comment.updated_at = datetime.now()

	save_comments_to_txt(db_comments, comment_path)
	return comment


# 5. Delete one comment
@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int) -> dict:
	refresh_mock_state()
	comment = find_comment(comment_id)

	if comment.user_id != CURRENT_USER_ID:
		raise HTTPException(status_code=403, detail="You can only delete your own comment")

	to_delete_ids = collect_comment_descendants(comment_id)
	remain_comments = [item for item in db_comments if item.comment_id not in to_delete_ids]
	db_comments.clear()
	db_comments.extend(remain_comments)

	save_comments_to_txt(db_comments, comment_path)
	return {"message": f"Deleted {len(to_delete_ids)} comment(s)"}