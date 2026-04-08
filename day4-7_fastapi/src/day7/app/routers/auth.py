import logging
import os
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi import Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db 
from app.models import User 
from app.schemas import UserRegister,UserLogin,TokenResponse
from app.core.dependencies import get_current_user, oauth2_scheme
from app.core.security import hash_password, verify_password, create_access_token, revoke_token

# Thay vì gắn thẳng vào app thì dùng router 
# để nhóm các endpoint lại trước theo logic 
router = APIRouter()

logger = logging.getLogger("app.auth")

ADMIN_REGISTER_KEY = os.getenv("ADMIN_REGISTER_KEY")


def send_welcome_notification(email: str, name: str) -> None:
    logger.info("[BG TASK] Welcome notification sent to %s <%s>", name, email)


def write_logout_audit(user_id: int) -> None:
    logger.info("[BG TASK] User %s logged out", user_id)

async def authenticate_user(email: str, password: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="Email not found !")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong password !")

    return user


async def create_user_account(request: UserRegister, role: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == request.email))
    find_email = result.scalars().first()
    if find_email is not None:
        raise HTTPException(status_code=409, detail="This email already exists !")

    user_to_db = User(
        name=request.name,
        email=request.email,
        hashed_password=hash_password(request.password),
        role=role,
    )
    db.add(user_to_db)
    await db.commit()
    await db.refresh(user_to_db)
    return user_to_db

# 1.1 POST /register
@router.post("/register")
async def register_app(request : UserRegister,
    background_tasks: BackgroundTasks,
    db : AsyncSession = Depends(get_db),             
    ):
    user_to_db = await create_user_account(request, "normal_user", db)

    payload = {"sub" : str(user_to_db.user_id), "role": user_to_db.role}
    jwt_token = create_access_token(payload)
    background_tasks.add_task(send_welcome_notification, user_to_db.email, user_to_db.name)
    
    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
    )

# 1.2 POST /register-admin
@router.post("/register-admin")
async def register_admin_app(
    request: UserRegister,
    background_tasks: BackgroundTasks,
    admin_key: str = Header(alias="X-Admin-Key"),
    db: AsyncSession = Depends(get_db),
):
    if not ADMIN_REGISTER_KEY:
        raise HTTPException(status_code=500, detail="ADMIN_REGISTER_KEY is not configured")

    if admin_key != ADMIN_REGISTER_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin registration key")

    user_to_db = await create_user_account(request, "admin", db)
    payload = {"sub": str(user_to_db.user_id), "role": user_to_db.role}
    jwt_token = create_access_token(payload)
    background_tasks.add_task(send_welcome_notification, user_to_db.email, user_to_db.name)

    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
    )
# 2. POST /login 
@router.post("/login")
async def login_app(request : UserLogin,
    db : AsyncSession = Depends(get_db),
    ):
    user = await authenticate_user(request.email, request.password, db)

    # Tạo JWT 
    payload = {"sub" : str(user.user_id), "role": user.role}
    jwt_token = create_access_token(payload)
    
    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
    )

# 3. POST /token (OAuth2 password flow cho Swagger Authorize)
@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    payload = {"sub": str(user.user_id), "role": user.role}
    jwt_token = create_access_token(payload)

    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
    )

# 4. POST /logout 
@router.post("/logout")
async def logout(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    revoke_token(token)
    background_tasks.add_task(write_logout_audit, current_user.user_id)
    return {"message": "Logout successful"}
    