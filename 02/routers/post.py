from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
import controllers
import models
import sqlite3

router = APIRouter(prefix="/posts", tags=["posts"])

con_post = sqlite3.connect("posts.db")
cur_post = con_post.cursor()
cur_post.execute("CREATE TABLE IF NOT EXISTS posts(ID, nickName, title, content, likes, \
comments, views, date, post_num INTEGER PRIMARY KEY)")
con_post.commit()

con_comment = sqlite3.connect("comments.db")
cur_comment = con_comment.cursor()
cur_comment.execute("CREATE TABLE IF NOT EXISTS comments(ID, nickName, content, likes, \
date, post_num)")
con_comment.commit()

@router.get("/page/{page_num}")
async def post_outside(page_num: int):
    return controllers.post_outside_controller(page_num, cur_post)

@router.get("/inside/{post_num}")
async def post_inside(post_num: int):
    try:
        result = controllers.post_inside_controller(page_num, cur_post, cur_comment)
        con_post.commit()
        return result

    except controllers.NoPostError:
        raise HTTPException(
			status_code=404,
			detail="존재하지 않는 게시글입니다."
		)

@router.post("/inside/{post_num}/like")
async def like(post_num: int):
    result = controllers.like_controller(post_num, cur_post)
    con_post.commit()
    return result
    
@router.post("/inside/{post_num}/comments")
async def comment(data: models.CommentCreate, post_num: int):
    try:
        return controllers.comment_controller(data, post_num, cur_comment)

    except:
        raise controllers.HTTPException(
            status_code=400,
            detail="댓글을 적어주세요"
        )

@router.post("/publish")
async def publish(data: models.PostCreate):
    try:
        return controllers.publish_controller(data, cur_post)
    except controllers.PostNamePatternError:
        raise HTTPException(
            status_code=400,
            detail="제목은 최대 20자 입니다."
        )
    except controllers.EmptyPost:
        raise HTTPException(
            status_code=400,
            detail="제목과 게시글을 적어주세요"
        )
