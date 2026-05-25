from pydantic import BaseModel
class UserCheck(BaseModel):
    user_id: str
    pwd: str

class PostCreate(BaseModel):
    check: UserCheck
    nickName: str
    title: str
    content: str
    
class CommentCreate(BaseModel):
    check: UserCheck
    nickName: str
    content: str
