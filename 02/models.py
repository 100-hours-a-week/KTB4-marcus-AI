from pydantic import BaseModel

class PostCreate(BaseModel):
    user_id: str
    nickName: str
    title: str
    content: str
    
class CommentCreate(BaseModel):
    user_id: str
    nickName: str
    content: str