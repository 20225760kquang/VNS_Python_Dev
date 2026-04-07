from datetime import datetime
from typing import List, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models import Blog, Comment, User
from app.schemas import BlogCommentListResponse, CommentCreate, CommentResponse, CommentUpdate

router = APIRouter()


def check_blog_visible(blog: Blog, user: User) -> None:
    if blog.author_id != user.user_id and blog.status != "published":
        raise HTTPException(status_code=403, detail="You cannot access comments of this draft blog")


async def find_blog(blog_id: int, db: AsyncSession) -> Blog:
    result = await db.execute(select(Blog).where(Blog.blog_id == blog_id))
    blog = result.scalars().first()
    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog


async def find_comment(comment_id: int, db: AsyncSession) -> Comment:
    result = await db.execute(select(Comment).where(Comment.comment_id == comment_id))
    comment = result.scalars().first()
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


def collect_comment_descendants(comment_id: int, comments: List[Comment]) -> Set[int]:
    children_map: dict[int, List[int]] = {}
    
    """ 
    Duyệt qua tất cả comment, thu được 1 dict gồm cha và danh sách các con cấp 1 ! 
    """
    for comment in comments:
        if comment.parent_id is None:
            continue
        children_map.setdefault(comment.parent_id, []).append(comment.comment_id)

    to_delete: Set[int] = set()
    stack = [comment_id]
    while stack:
        current = stack.pop()
        if current in to_delete:
            continue
        to_delete.add(current)
        stack.extend(children_map.get(current, []))

    return to_delete


# 1. Comment a blog or reply a comment
@router.post("/blogs/{blog_id}/comments", response_model=CommentResponse)
async def create_comment(
    blog_id: int,
    request: CommentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Comment:
    blog = await find_blog(blog_id, db)
    check_blog_visible(blog, user)

    parent_id = request.parent_id
    if parent_id is not None:
        parent = await find_comment(parent_id, db)
        if parent.blog_id != blog_id:
            raise HTTPException(status_code=400, detail="parent_id must belong to the same blog")

    new_comment = Comment(
        user_id=user.user_id,
        blog_id=blog_id,
        parent_id=parent_id,
        content=request.content,
        created_at=datetime.now(),
        updated_at=None,
    )

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment


# 2. Get comments of one blog
@router.get("/blogs/{blog_id}/comments", response_model=BlogCommentListResponse)
async def get_blog_comments(
    blog_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BlogCommentListResponse:
    blog = await find_blog(blog_id, db)
    check_blog_visible(blog, user)

    count_result = await db.execute(select(Comment).where(Comment.blog_id == blog_id))
    total = len(count_result.scalars().all())

    comments_result = await db.execute(
        select(Comment).where(Comment.blog_id == blog_id).order_by(Comment.comment_id).offset((page - 1) * limit).limit(limit)
    )
    comments = comments_result.scalars().all()

    return BlogCommentListResponse(data=comments, page=page, limit=limit, total=total)


# 3. Get one comment
@router.get("/comments/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Comment:
    comment = await find_comment(comment_id, db)
    blog = await find_blog(comment.blog_id, db)
    check_blog_visible(blog, user)
    return comment


# 4. Update one comment
@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    request: CommentUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Comment:
    comment = await find_comment(comment_id, db)

    if comment.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="You can only update your own comment")

    comment.content = request.content
    comment.updated_at = datetime.now()

    await db.commit()
    await db.refresh(comment)
    return comment


# 5. Delete one comment
@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    comment = await find_comment(comment_id, db)

    if comment.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own comment")

    blog = await find_blog(comment.blog_id, db)
    check_blog_visible(blog, user)

    all_comments_result = await db.execute(select(Comment).where(Comment.blog_id == comment.blog_id))
    all_comments = all_comments_result.scalars().all()
    to_delete_ids = collect_comment_descendants(comment_id, all_comments)

    await db.execute(delete(Comment).where(Comment.comment_id.in_(to_delete_ids)))
    await db.commit()

    return {"message": f"Deleted {len(to_delete_ids)} comment(s)"}
