from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from app.models import Blog, Comment, User 
from app.schemas import BlogCreate, BlogListResponse, BlogResponse, BlogUpdate
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db 
from app.core.dependencies import get_current_user 

router = APIRouter()

ALLOWED_BLOG_STATUS = {"draft", "published"}

def validate_status(status: str) -> None:
    if status not in ALLOWED_BLOG_STATUS:
        raise HTTPException(status_code=400, detail="status must be draft or published")
    
# 1. Create new blog
@router.post("/blogs", response_model=BlogResponse)
async def create_blog(request: BlogCreate,
    user : User = Depends(get_current_user),
    db : AsyncSession = Depends(get_db)) -> Blog:
    
    validate_status(request.status)

    now = datetime.now()
    published_at = now if request.status == "published" else None

    new_blog = Blog(
        title=request.title,
        content=request.content,
        created_at=now,
        status=request.status,
        published_at=published_at,
        updated_at=None,
        author_id=user.user_id,
    )
    db.add(new_blog)
    await db.commit()
    await db.refresh(new_blog)
    
    return new_blog


# 2. View one blog
@router.get("/blogs/{blog_id}", response_model=BlogResponse)
async def get_blog(blog_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)) -> Blog:
    
    result = await db.execute(select(Blog).where(Blog.blog_id == blog_id))
    blog = result.scalars().first()

    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")

    if blog.author_id != user.user_id and blog.status != "published":
        raise HTTPException(status_code=403, detail="You cannot view this draft blog")

    return blog

# 3. View all blogs of one user
@router.get("/users/{user_id}/blogs", response_model=BlogListResponse)
async def get_user_blogs(
    user_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db) 
) -> BlogListResponse:
    
    
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    if user_result.scalars().first() is None:  
        raise HTTPException(status_code=404, detail="User not found")

    filters = [Blog.author_id == user_id]
    if user.user_id != user_id:
        filters.append(Blog.status == "published")

    total_result = await db.execute(select(Blog).where(*filters))
    total = len(total_result.scalars().all())
    start = (page - 1) * limit
    blogs_result = await db.execute(
        select(Blog).where(*filters).order_by(Blog.blog_id).offset(start).limit(limit)
    )
    blogs = blogs_result.scalars().all()

    return BlogListResponse(data=blogs, page=page, limit=limit, total=total)


# 4. Update one blog
@router.put("/blogs/{blog_id}", response_model=BlogResponse)
async def update_blog(blog_id: int, 
    request: BlogUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)) -> Blog:
    
    result = await db.execute(select(Blog).where(Blog.blog_id == blog_id))
    blog = result.scalars().first()

    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")

    if blog.author_id != user.user_id:
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

    await db.commit()
    await db.refresh(blog)
    
    return blog


# 5. Delete one blog
@router.delete("/blogs/{blog_id}")
async def delete_blog(
    blog_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Blog).where(Blog.blog_id == blog_id))
    blog = result.scalars().first()

    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")

    if blog.author_id != user.user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own blog")

    await db.execute(delete(Comment).where(Comment.blog_id == blog_id))
    await db.delete(blog)
    await db.commit()

    return {"message": f"Deleted blog {blog_id} and related comments"}
