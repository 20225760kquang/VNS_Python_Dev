from fastapi import FastAPI

from app.core.middleware import setup_middlewares
from app.routers import auth, blogs, comments

app = FastAPI(title="Blog API")

setup_middlewares(app)

# Gắn routers
app.include_router(blogs.router)
app.include_router(comments.router)
app.include_router(auth.router)