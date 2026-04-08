from fastapi import Depends, HTTPException, status 
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User 
from app.core.security import SECRET_KEY,ALGORITHM, is_token_revoked

# Dùng OAuth2 token endpoint chuẩn để Swagger tự động LẤY/GẮN bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token : str = Depends(oauth2_scheme),
    db : AsyncSession = Depends(get_db)                 
    ):
    if is_token_revoked(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # 1.Decode token 
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    
        # 2.Check payload (dữ liệu bên trong token)
        if user_id is None:
            # Throw exceptions
            raise HTTPException(status_code=401, detail="Unauthorized")
    except JWTError: # Trường hợp khi token hết hạn hoặc sai
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 3.Query trong DB 
    result = await db.execute(select(User).where(User.user_id == int(user_id)))
    user = result.scalars().first()
    if user is None: 
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user 