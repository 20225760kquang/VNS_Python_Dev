from fastapi import FastAPI
from routers import blogs, comments

app = FastAPI(title="Blog API")

# Gắn routers
app.include_router(blogs.router)
app.include_router(comments.router)