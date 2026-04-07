from dotenv import load_dotenv 
import os 
from passlib.context import CryptContext
from jose import jwt 
from datetime import datetime, timedelta, timezone 

# Blacklist token trong runtime để hỗ trợ logout JWT (áp dụng cho 1 process)
REVOKED_TOKENS: set[str] = set()

# 1.Đọc config từ .env 
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# 2.Setup bcrypt context tức dùng thuật toán bcrypt để hashing 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 3.Encode -> hash password 
def hash_password(password: str) -> str : 
    return pwd_context.hash(password)

# 4.Verify tức so sánh giữa pass thường và pass đã được encode lưu ở DB 
def verify_password(plain_pwd : str, hashed_pwd : str) -> bool : 
    return pwd_context.verify(plain_pwd,hashed_pwd)

# 5.Sinh JWT 
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    # Biến expire tính thời điểm hết hạn token
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Nhúng thời gian hết hạn vào payload 
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

# 6. Thu hồi token
def revoke_token(token: str) -> None:
    REVOKED_TOKENS.add(token)

# 7. Kiểm tra token đã bị thu hồi hay chưa 
def is_token_revoked(token: str) -> bool:
    return token in REVOKED_TOKENS


if __name__ == '__main__':
    # demo_bcrypt = "QNK1234xxxaaf56"
    # print(hash_password(demo_bcrypt))
    
    data = {"sub" : "2k12k22k32k4"}
    token = create_access_token(data)
    print(token)
    token_decode = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
    print(token_decode)
    
