from sqlalchemy import Column,String,Integer,Boolean,DateTime,ForeignKey,PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func 
from sqlalchemy.ext.declarative import declarative_base

# Base : Class cha mà mọi models kế thừa 
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer,primary_key=True,index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    blogs = relationship("Blog", back_populates="owner")
    comments = relationship("Comment", back_populates="user")
    
class Blog(Base):
    __tablename__ = "blogs"
    
    # Tham số "index" tự động cập nhật cho trường này khi có bản ghi mới thêm vào ! 
    blog_id = Column(Integer,primary_key=True,index = True)
    title = Column(String,nullable=False)
    content = Column(String,nullable=False)
    created_at = Column(DateTime,server_default=func.now())
    # Trường status có 2 giá trị là : "draft" & "published" 
    status = Column(String,nullable=False)
    # Chuyển status từ "draft" -> "published"
    published_at = Column(DateTime,nullable=True)
    # Cập nhật khi thực hiện endpoint có method PATCH/UPDATE
    updated_at = Column(DateTime)    
    # Foreign key 
    author_id = Column(Integer,ForeignKey("users.user_id"), nullable=False)
    
    owner = relationship("User", back_populates="blogs")
    comments = relationship("Comment", back_populates="blog")
    
class Comment(Base):

    __tablename__ = "comments"
    
    comment_id = Column(Integer,primary_key=True,index = True)
    
    # Foreign key 
    user_id = Column(Integer,ForeignKey("users.user_id"), nullable=False)
    blog_id = Column(Integer,ForeignKey("blogs.blog_id"), nullable=False)
    parent_id = Column(Integer,ForeignKey("comments.comment_id"), nullable=True)
    
    content = Column(String,nullable=False)
    created_at = Column(DateTime,server_default=func.now())
    updated_at = Column(DateTime)

    user = relationship("User", back_populates="comments")
    blog = relationship("Blog", back_populates="comments")
    parent = relationship("Comment", remote_side=[comment_id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent")
    
"""
- Relationship giúp SQLAlchemy biết cách để join 2 bảng truy cập dữ liệu 1 cách tiện lợi !!!

- Tham số "back_populates" dùng để khai báo 2 chiều của cùng 1 relationship trong SQLAlchemy

- Tham số "remote_site" dùng cho self-referential relationship (bảng tự liên kết với chính nó)
"""