from datetime import datetime
from pathlib import Path
import sys
import asyncio

from dotenv import load_dotenv
from sqlalchemy import delete

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from app.core.security import hash_password
from app.database import Base, engine, session_local
from app.models import Blog, Comment, User


load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=True)

""" 
Hàm sinh dữ liệu giả, lưu vào db với db_url có trong .env 
"""

async def seed_data() -> None:
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)

	async with session_local() as db:
		try:
			await db.execute(delete(Comment))
			await db.execute(delete(Blog))
			await db.execute(delete(User))
			await db.commit()

			users = [
				User(
					name="Alice Nguyen",
					email="alice@example.com",
					hashed_password=hash_password("Alice1234"),
				),
				User(
					name="Bob Tran",
					email="bob@example.com",
					hashed_password=hash_password("Bob12345"),
				),
				User(
					name="Charlie Pham",
					email="charlie@example.com",
					hashed_password=hash_password("Charlie123"),
				),
			]

			db.add_all(users)
			await db.flush()

			now = datetime.now()
			blogs = [
				Blog(
					title="Getting started with FastAPI",
					content="A practical introduction to FastAPI, dependencies, and routing.",
					created_at=now,
					status="published",
					published_at=now,
					updated_at=None,
					author_id=users[0].user_id,
				),
				Blog(
					title="SQLAlchemy session patterns",
					content="How to structure session usage, commits, and refresh calls.",
					created_at=now,
					status="published",
					published_at=now,
					updated_at=None,
					author_id=users[0].user_id,
				),
				Blog(
					title="Draft: Auth flow notes",
					content="Internal notes about hashing, JWT, and request validation.",
					created_at=now,
					status="draft",
					published_at=None,
					updated_at=None,
					author_id=users[1].user_id,
				),
			]

			db.add_all(blogs)
			await db.flush()

			first_comment = Comment(
				user_id=users[1].user_id,
				blog_id=blogs[0].blog_id,
				parent_id=None,
				content="This helped me understand the structure clearly.",
				created_at=now,
				updated_at=None,
			)
			second_comment = Comment(
				user_id=users[2].user_id,
				blog_id=blogs[0].blog_id,
				parent_id=None,
				content="Good overview. Can you add an example for pagination?",
				created_at=now,
				updated_at=None,
			)
			third_comment = Comment(
				user_id=users[0].user_id,
				blog_id=blogs[1].blog_id,
				parent_id=None,
				content="Session refresh is often overlooked but very important.",
				created_at=now,
				updated_at=None,
			)

			db.add_all([first_comment, second_comment, third_comment])
			await db.flush()

			reply_comment = Comment(
				user_id=users[0].user_id,
				blog_id=blogs[0].blog_id,
				parent_id=first_comment.comment_id,
				content="I will add that in the next update.",
				created_at=now,
				updated_at=None,
			)

			db.add(reply_comment)
			await db.commit()

			print("Seed completed: 3 users, 3 blogs, 4 comments")
		except Exception:
			await db.rollback()
			raise


if __name__ == "__main__":
	asyncio.run(seed_data())
