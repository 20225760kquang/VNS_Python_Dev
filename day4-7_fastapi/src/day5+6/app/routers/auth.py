from fastapi import APIRouter, Depends, HTTPException
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


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="Email not found !")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong password !")

    return user

# 1. POST /register
@router.post("/register")
async def register_app(request : UserRegister,
    db : AsyncSession = Depends(get_db),             
    ):
    # 1.Check email 
    result = await db.execute(select(User).where(User.email == request.email))
    find_email = result.scalars().first()
    if find_email is not None : 
        raise HTTPException(status_code = 409, detail="This email already exists !" )
    # 2.Khi email được accept, ta sẽ encode password 
    hashed_pwd = hash_password(request.password)
    # 3.Lưu user vào db
    user_to_db = User(
        name = request.name,
        email = request.email,
        hashed_password = hashed_pwd,
    )
    db.add(user_to_db)
    await db.commit()
    await db.refresh(user_to_db)
    # 4. Tạo JWT 
    payload = {"sub" : str(user_to_db.user_id)}
    jwt_token = create_access_token(payload)
    
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

    # 3.Generate JWT 
    payload = {"sub" : str(user.user_id)}
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
    payload = {"sub": str(user.user_id)}
    jwt_token = create_access_token(payload)

    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
    )


@router.post("/logout")
async def logout(
    _: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    revoke_token(token)
    return {"message": "Logout successful"}
    