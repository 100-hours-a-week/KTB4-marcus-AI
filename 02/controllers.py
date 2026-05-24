import sqlite3
from pydantic import BaseModel
from datetime import datetime
import models
import re

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

def login_controller(user_id: str, pwd: str, cur_user):
    if not EMAIL_PATTERN.match(user_id):
        raise EmailPatternError()
    
    res_user = cur_user.execute("SELECT ID, pwd, nickName FROM users \
    WHERE ID=? AND pwd=?", (user_id, pwd))
    user_data = res_user.fetchone()

    if user_data is None:
        raise IDPasswordIncorrectError()
    
    return {"user_id": user_id, "nickName": user_data[2]}

def signup_controller(user_id: str, pwd: str, pwd_again: str, nickName: str, cur_user):
    if not EMAIL_PATTERN.match(user_id):
        raise EmailPatternError()
    
    res_user = cur_user.execute("SELECT ID FROM users WHERE ID=?", (user_id,))

    if res_user.fetchone() is not None:
	    raise IDAlreadyExists()

    if not PWD_PATTERN.match(pwd):
	    raise PasswordPatternError()
    
    if pwd != pwd_again:
        raise PasswordAgainError()
    
    cur_user.execute("INSERT INTO users (ID, pwd, nickName) \
    VALUES (?, ?, ?)", (user_id, pwd, nickName))

    return {"message": "회원가입 성공"}

# ====================================

def post_outside_controller(page_num: int, cur_post):
    pass_num = 10 * (page_num - 1)
    res_post = cur_post.execute("SELECT ID, nickName, title, likes, \
    comments, views, date, post_num FROM posts \
    ORDER BY post_num DESC LIMIT ?, 10", (pass_num,))

    visible_posts = res.fetchall()

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
    con_post.commit()

    res_post = cur_post.execute("SELECT likes FROM posts WHERE post_num=?", (post_num,))
    likes_data = res_post.fetchone()

    return {"likes": likes_data[0]}

def comment_controller(data: models.CommentCreate, post_num: int, cur_comment):
    if not data.content:
        raise EmptyComment()
    
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M:%S")

    cur_comment.execute("INSERT INTO comments(ID, nickName, \
    content, likes, date), VALUES (?, ?, ?, 0, ?, ?)", \
    (data.user_id, data.nickName, data.content, formatted_date, post_num))

    return None

def publish_controller(data: models.PostCreate, cur_post):
    if len(data.title) > 20:
        raise PostNamePatternError()
    if not data.title or not data.content:
        raise EmptyPost()
    
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d %H:%M:%S")

    cur_post.execute("INSERT INTO posts (ID, nickName, title, content, \
    likes, comments, views, date), \
    VALUES (?, ?, ?, ?, 0, 0, 0, ?)", \
    (data.user_id, data.nickName, data.title, data.content, formatted_date))

    return None