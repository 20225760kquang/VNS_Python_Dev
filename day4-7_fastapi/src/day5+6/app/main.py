from fastapi import FastAPI

from app.routers import auth, blogs, comments

app = FastAPI(title="Blog API")

# Gắn routers
app.include_router(blogs.router)
app.include_router(comments.router)
app.include_router(auth.router)