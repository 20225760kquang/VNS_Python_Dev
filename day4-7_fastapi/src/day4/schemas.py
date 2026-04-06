from pydantic import BaseModel, Field
from typing import Optional,List
from datetime import datetime 


class BlogCreate(BaseModel):
    title : str 
    content : str
    status : str # ["draft", "published"]
        

class BlogUpdate(BaseModel):
    title : Optional[str] = None 
    content : Optional[str] = None  
    status : Optional[str] = None

class BlogResponse(BaseModel):
    blog_id : int 
    title : str 
    content : str  
    status : str 
    created_at : datetime
    published_at : Optional[datetime] = None
    updated_at : Optional[datetime] = None
    author_id : int
    
    class Config:
        from_attributes = True

class BlogListResponse(BaseModel):
    data : List[BlogResponse]
    page : int 
    limit : int = Field(default=10,ge=1,le=100)
    total : int     

class CommentCreate(BaseModel):
    content : str
    parent_id : Optional[int] = None 

class CommentUpdate(BaseModel): 
    content : str 
    
class CommentResponse(BaseModel): 
    comment_id : int 
    blog_id : int
    user_id : int  
    parent_id : Optional[int] = None
    content : str 
    created_at : datetime
    updated_at : Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
class BlogCommentListResponse(BaseModel): 
    data : List[CommentResponse]
    page : int 
    limit : int = Field(default=10,ge=1,le=100)
    total : int     