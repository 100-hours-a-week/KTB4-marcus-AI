from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
import controllers
import models
import sqlite3

router = APIRouter(prefix="/posts", tags=["posts"])

con_user = sqlite3.connect("users.db")
cur_user = con_user.cursor()
cur_user.execute("CREATE TABLE IF NOT EXISTS users(ID, pwd, nickName)")
con_user.commit()

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
    global cur_post
    return controllers.post_outside_controller(page_num, cur_post)

@router.get("/inside/{post_num}")
async def post_inside(post_num: int):
    global cur_post, cur_comment
    try:
        result = controllers.post_inside_controller(post_num, cur_post, cur_comment)
        con_post.commit()
        return result

    except controllers.NoPostError:
        raise HTTPException(
			status_code=404,
			detail="존재하지 않는 게시글입니다."
		)

@router.post("/inside/{post_num}/like")
async def like(post_num: int):
    global cur_post
    result = controllers.like_controller(post_num, cur_post)
    con_post.commit()
    return result
    
@router.post("/inside/{post_num}/comments")
async def comment(data: models.CommentCreate, post_num: int):
    global cur_user, cur_comment
    try:
        result = controllers.comment_controller(data, post_num, cur_user, cur_comment)
        con_comment.commit()
        return result
    except controllers.IDPasswordIncorrectError:
        raise HTTPException(
            status_code=404,
            detail="아이디 또는 비밀번호가 잘못되었습니다"
        )
    except controllers.EmptyComment:
        raise HTTPException(
            status_code=400,
            detail="댓글을 적어주세요"
        )

@router.get("/inside/{post_num}/summary")
async def summary(post_num: int):
    global cur_post
    try:
        return controllers.summary_controller(post_num, cur_post)

    except controllers.AIBadCodeError:
        raise HTTPException(
            status_code=503,
            detail="AI 요약을 받지 못했습니다"
        )
    except controllers.AIOfflineError:
        raise HTTPException(
            status_code=503,
            detail="AI 서버가 작동하지 않습니다"
        )

@router.put("/inside/{post_num}/revise")
async def revise(data: models.PostCreate, post_num: int):
    global cur_user, cur_post
    try:
        result = controllers.revise_controller(data, post_num, cur_user, cur_post)
        con_post.commit()
        return result
    except controllers.IDPasswordIncorrectError:
        raise HTTPException(
            status_code=404,
            detail="아이디 또는 비밀번호가 잘못되었습니다"
        )
    except controllers.PostNamePatternError:
        raise HTTPException(
            status_code=400,
            detail="제목은 최대 20자 입니다."
        )
    except controllers.EmptyPost:
        raise HTTPException(
            status_code=503,
            detail="제목과 게시글을 적어주세요"
        )

@router.delete("/inside/{post_num}/delete")
async def delete(data: models.UserCheck, post_num: int):
    global cur_user, cur_post
    try:
        result = controllers.delete_controller(data, post_num, cur_user, cur_post)
        con_post.commit()
        return result
    except controllers.IDPasswordIncorrectError:
        raise HTTPException(
            status_code=404,
            detail="아이디 또는 비밀번호가 잘못되었습니다"
        )

@router.post("/publish")
async def publish(data: models.PostCreate):
    global cur_user, cur_post
    try:
        result = controllers.publish_controller(data, cur_user, cur_post)
        con_post.commit()
        return result
    except controllers.IDPasswordIncorrectError:
        raise HTTPException(
            status_code=404,
            detail="아이디 또는 비밀번호가 잘못되었습니다"
        )
    except controllers.PostNamePatternError:
        raise HTTPException(
            status_code=400,
            detail="제목은 최대 20자 입니다."
        )
    except controllers.EmptyPost:
        raise HTTPException(
            status_code=503,
            detail="제목과 게시글을 적어주세요"
        )
