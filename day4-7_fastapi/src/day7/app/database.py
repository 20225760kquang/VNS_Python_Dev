from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv 
from pathlib import Path
import os 


load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

# 1.Engine : Kết nối Python & SQL Database (Postgresql)

# Nhận diện context: ENVIRONMENT=docker hoặc ENVIRONMENT=local
environment = os.getenv("ENVIRONMENT", "local").lower()
if environment == "docker":
    database_url = os.getenv("DOCKER_DATABASE_URL")
else:
    database_url = os.getenv("LOCAL_DATABASE_URL") 
    
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(database_url, echo=False)
# 2.SessionLocal : Mỗi request tới API sẽ mở 1 session để làm việc với DB 
session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 3.Base : Class cha mà mọi models kế thừa 
Base = declarative_base()

async def get_db(): # mở session cho mỗi lần xử lí requests
    async with session_local() as db:
        yield db