import sqlite3
from pydantic import BaseModel
from datetime import datetime
import models
import re
import httpx
import json

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.com$")
PWD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\~\!\@\#\$\%\^\&\*\|\'\"\;\:\₩\\\?]).{8,20}$")

class NoPostError(Exception): pass
class EmailPatternError(Exception): pass
class IDPasswordIncorrectError(Exception): pass
class IDAlreadyExists(Exception): pass
class PasswordPatternError(Exception): pass
class PasswordAgainError(Exception): pass
class EmptyComment(Exception): pass
class PostNamePatternError(Exception): pass
class EmptyPost(Exception): pass
class AIBadCodeError(Exception): pass
class AIOfflineError(Exception): pass

def login_checker(data: models.UserCheck, cur_user):
    res_user = cur_user.execute("SELECT ID, pwd, nickName FROM users \
    WHERE ID=? AND pwd=?", (data.user_id, data.pwd))
    user_data = res_user.fetchone()

    if user_data is None:
        raise IDPasswordIncorrectError()
    
    return user_data

def signup_controller(data: models.UserCheck, pwd_again: str, nickName: str, cur_user):
    if not EMAIL_PATTERN.match(data.user_id):
        raise EmailPatternError()
    
    res_user = cur_user.execute("SELECT ID FROM users WHERE ID=?", (data.user_id,))

    if res_user.fetchone() is not None:
	    raise IDAlreadyExists()

    if not PWD_PATTERN.match(data.pwd):
	    raise PasswordPatternError()
    
    if data.pwd != pwd_again:
        raise PasswordAgainError()
    
    cur_user.execute("INSERT INTO users (ID, pwd, nickName) \
    VALUES (?, ?, ?)", (data.user_id, data.pwd, nickName))

    return {"message": "회원가입 성공"}

# ====================================

def post_outside_controller(page_num: int, cur_post):
    pass_num = 10 * (page_num - 1)
    res_post = cur_post.execute("SELECT ID, nickName, title, likes, \
    comments, views, date, post_num FROM posts \
    ORDER BY post_num DESC LIMIT ?, 10", (pass_num,))

    visible_posts = res_post.fetchall()

    posts_list = []

    for post_data in visible_posts:
        post_dict = {
            "poster_id": post_data[0],
            "nickName": post_data[1],
            "title": post_data[2],
            "likes": post_data[3],
            "comments": post_data[4],
            "views": post_data[5],
            "date": post_data[6],
            "post_num": post_data[7]
        }
        posts_list.append(post_dict)
    
    return {"posts_list": posts_list, "page_num": page_num}

def post_inside_controller(post_num: int, cur_post, cur_comment):
    res_post = cur_post.execute("SELECT * FROM posts WHERE post_num=?", (post_num,))
    post_data = res_post.fetchone()

    if post_data is None:
        raise NoPostError()
    
    cur_post.execute("UPDATE posts SET views = views + 1 \
    WHERE post_num = ?", (post_num,))

    post_dict = {
            "poster_id": post_data[0],
            "nickName": post_data[1],
            "title": post_data[2],
            "content": post_data[3],
            "likes": post_data[4],
            "comments": post_data[5],
            "views": post_data[6],
            "date": post_data[7],
        }

    res_comment = cur_comment.execute("SELECT * FROM comments WHERE post_num=? \
    ORDER BY date", (post_num,))
    visible_comments = res_comment.fetchall()

    comments_list = []

    for comment_data in visible_comments:
        comment_dict = {
            "commenter_id": comment_data[0],
            "nickName": comment_data[1],
            "content": comment_data[2],
            "likes": comment_data[3],
            "date": comment_data[4],
        }
        comments_list.append(comment_dict)

    return {"current_post": post_dict, "comments_list": comments_list}

def like_controller(post_num: int, cur_post):
    cur_post.execute("UPDATE posts SET likes = likes + 1 \
    WHERE post_num = ?", (post_num,))

    return {"message": "좋아요 성공!"}

def comment_controller(data: models.CommentCreate, post_num: int, cur_user, cur_comment):
    login_checker(data.check, cur_user)
    
    if not data.content:
        raise EmptyComment()
    
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M:%S")

    cur_comment.execute("INSERT INTO comments(ID, nickName, \
    content, likes, date, post_num) VALUES (?, ?, ?, ?, ?, ?)", \
    (data.check.user_id, data.nickName, data.content, 0, formatted_date, post_num))

    return {"message": "댓글 성공!"}

def summary_controller(post_num: int, cur_post):
    res_post = cur_post.execute("SELECT content FROM posts WHERE post_num=?", (post_num,))
    content = res_post.fetchone()[0]

    url = "http://localhost:11434/v1/chat/completions"

    headers = {
	"Content-Type": "application/json"
    }

    payload = {
        "model": "gemma4:e4b",
        "messages": [
            {
                "role": "system",
                "content": "당신은 커뮤니티에 올라오는 글을 한 문장에서 두 문장으로 정리해주는 전문가입니다. \
                유저의 본문을 핵심을 요약하여 한국어로 한 문장으로 정리해주세요."
            },
            {
                "role": "user",
                "content": content
            }
        ],
        "stream": False
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)

        if response.status_code != 200:
            raise AIBadCodeError()

        return {"summary": response.json()["choices"][0]["message"]["content"]}

    except Exception:
        raise AIOfflineError()

def revise_controller(data: models.PostCreate, post_num: int, cur_user, cur_post):
    login_checker(data.check, cur_user)

    if len(data.title) > 20:
        raise PostNamePatternError()
    if not data.title or not data.content:
        raise EmptyPost()
    
    cur_post.execute("UPDATE posts SET title = ?, content = ? \
    WHERE post_num = ?", (data.title, data.content, post_num))

    return {"message": "게시글 수정 성공!"}

def delete_controller(data: models.UserCheck, post_num: int, cur_user, cur_post):
    login_checker(data, cur_user)
    cur_post.execute("DELETE FROM posts WHERE post_num = ?", (post_num,))
    return {"message": "게시글 삭제 성공!"}

def publish_controller(data: models.PostCreate, cur_user, cur_post):
    login_checker(data.check, cur_user)
    if len(data.title) > 20:
        raise PostNamePatternError()
    if not data.title or not data.content:
        raise EmptyPost()
    
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M:%S")

    cur_post.execute("INSERT INTO posts (ID, nickName, title, content, \
    likes, comments, views, date) \
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)", \
    (data.check.user_id, data.nickName, data.title, data.content, 0, 0, 0, formatted_date))

    return {"message": "포스트 작성 성공!"}
