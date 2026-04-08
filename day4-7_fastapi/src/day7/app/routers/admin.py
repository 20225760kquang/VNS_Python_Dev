import os
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin
from app.core.security import hash_password
from app.database import get_db
from app.models import User, Blog
from app.schemas import AdminRegister, UserResponse, UserRoleUpdate, AdminUserBlogListResponse, BlogResponse

# Hiển thị được trên API Swaggers
router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_REGISTER_KEY = os.getenv("ADMIN_REGISTER_KEY")

@router.post("/register", response_model=UserResponse)
async def register_admin(
    request: AdminRegister,
    admin_key: str = Header(alias="X-Admin-Key"),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not ADMIN_REGISTER_KEY:
        raise HTTPException(status_code=500, detail="ADMIN_REGISTER_KEY is not configured")

    if admin_key != ADMIN_REGISTER_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin registration key")

    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalars().first()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="This email already exists !")

    admin_user = User(
        name=request.name,
        email=request.email,
        hashed_password=hash_password(request.password),
        role="admin",
    )

    db.add(admin_user)
    await db.commit()
    await db.refresh(admin_user)
    return admin_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    result = await db.execute(select(User).order_by(User.user_id))
    return list(result.scalars().all())


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    request: UserRoleUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> User:
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if current_admin.user_id == user.user_id and request.role.value != "admin":
        raise HTTPException(status_code=400, detail="You cannot remove your own admin role")

    user.role = request.role.value
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/users/{user_id}/blogs-all", response_model=AdminUserBlogListResponse)
async def get_user_all_blogs(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserBlogListResponse:
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    query = select(Blog).where(Blog.author_id == user_id)

    if start_date:
        query = query.where(Blog.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.where(Blog.created_at <= datetime.combine(end_date, datetime.max.time()))

    query = query.order_by(Blog.blog_id)
    blogs_result = await db.execute(query)
    blogs = list(blogs_result.scalars().all())

    return AdminUserBlogListResponse(
        user_id=user.user_id,
        user_name=user.name,
        user_email=user.email,
        blogs=[BlogResponse.model_validate(blog) for blog in blogs],
        total=len(blogs),
        start_date=start_date,
        end_date=end_date,
    )
