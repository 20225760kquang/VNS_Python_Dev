from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Query

from models import Blog, Comment
from schemas import BlogCreate, BlogListResponse, BlogResponse, BlogUpdate
from utils.load_txt import load_mock_data
from utils.save_txt import save_blogs_to_txt, save_comments_to_txt


router = APIRouter()

CURRENT_USER_ID = 1
ALLOWED_BLOG_STATUS = {"draft", "published"}

default_data_path = Path(__file__).resolve().parents[1] / "mock_data"
loaded = load_mock_data(mock_data_dir=str(default_data_path))

db_users = loaded["users"]
db_blogs: List[Blog] = loaded["blogs"]
db_comments: List[Comment] = loaded["comments"]

blog_path = default_data_path / "blogs.txt"
comment_path = default_data_path / "comments.txt"


def find_blog(blog_id: int) -> Blog:
    blog = next((item for item in db_blogs if item.blog_id == blog_id), None)
    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog


def validate_status(status: str) -> None:
    if status not in ALLOWED_BLOG_STATUS:
        raise HTTPException(status_code=400, detail="status must be draft or published")
    
# 1. Create new blog
@router.post("/blogs", response_model=BlogResponse)
def create_blog(request: BlogCreate) -> Blog:
    validate_status(request.status)

    now = datetime.now()
    next_blog_id = max((blog.blog_id for blog in db_blogs), default=0) + 1
    published_at = now if request.status == "published" else None

    new_blog = Blog(
        blog_id=next_blog_id,
        title=request.title,
        content=request.content,
        created_at=now,
        status=request.status,
        published_at=published_at,
        updated_at=None,
        author_id=CURRENT_USER_ID,
    )

    db_blogs.append(new_blog)
    save_blogs_to_txt(db_blogs, blog_path)
    return new_blog


# 2. View one blog
@router.get("/blogs/{blog_id}", response_model=BlogResponse)
def get_blog(blog_id: int) -> Blog:
    blog = find_blog(blog_id)

    if blog.author_id != CURRENT_USER_ID and blog.status != "published":
        raise HTTPException(status_code=403, detail="You cannot view this draft blog")

    return blog


# 3. View all blogs of one user
@router.get("/users/{user_id}/blogs", response_model=BlogListResponse)
def get_user_blogs(
    user_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
) -> BlogListResponse:
    if not any(user.user_id == user_id for user in db_users):
        raise HTTPException(status_code=404, detail="User not found")

    blogs = [blog for blog in db_blogs if blog.author_id == user_id]
    if user_id != CURRENT_USER_ID:
        blogs = [blog for blog in blogs if blog.status == "published"]

    blogs = sorted(blogs, key=lambda item: item.blog_id)
    total = len(blogs)
    start = (page - 1) * limit
    end = start + limit

    return BlogListResponse(data=blogs[start:end], page=page, limit=limit, total=total)


# 4. Update one blog
@router.put("/blogs/{blog_id}", response_model=BlogResponse)
def update_blog(blog_id: int, request: BlogUpdate) -> Blog:
    blog = find_blog(blog_id)

    if blog.author_id != CURRENT_USER_ID:
        raise HTTPException(status_code=403, detail="You can only update your own blog")

    previous_status = blog.status

    if request.status is not None:
        validate_status(request.status)

    if request.title is not None:
        blog.title = request.title
    if request.content is not None:
        blog.content = request.content

    now = datetime.now()
    if request.status is not None:
        blog.status = request.status
        if previous_status == "draft" and request.status == "published":
            blog.published_at = now
            blog.updated_at = now
        elif request.status == "draft":
            blog.published_at = None
            blog.updated_at = now
        else:
            blog.updated_at = now
    else:
        blog.updated_at = now

    save_blogs_to_txt(db_blogs, blog_path)
    return blog


# 5. Delete one blog
@router.delete("/blogs/{blog_id}")
def delete_blog(blog_id: int) -> dict:
    blog = find_blog(blog_id)

    if blog.author_id != CURRENT_USER_ID:
        raise HTTPException(status_code=403, detail="You can only delete your own blog")

    db_blogs.remove(blog)

    # Remove comments that belong to deleted blog to keep mock data consistent.
    remain_comments = [comment for comment in db_comments if comment.blog_id != blog_id]
    db_comments.clear()
    db_comments.extend(remain_comments)

    save_blogs_to_txt(db_blogs, blog_path)
    save_comments_to_txt(db_comments, comment_path)

    return {"message": f"Deleted blog {blog_id} and related comments"}
