from fastapi import FastAPI, HTTPException, APIRouter
import sqlite3
import controllers
import models

router = APIRouter(prefix="/login", tags=["login"])

con_user = sqlite3.connect("users.db")
cur_user = con_user.cursor()
cur_user.execute("CREATE TABLE IF NOT EXISTS users(ID, pwd, nickName)")

@router.post("/signup")
async def signup(data: models.UserCheck, pwd_again: str, nickName: str):
	global cur_user
	try:
		result = controllers.signup_controller(data, pwd_again, nickName, cur_user)
		con_user.commit()
		return result
	
	except controllers.EmailPatternError:
		raise HTTPException(
			status_code=400,
			detail="올바른 이메일 주소 형식을 입력해주세요. \
			(예: example\@example.com)"
		)

	except controllers.IDAlreadyExists:
		raise HTTPException(
			status_code=409,
			detail="중복된 이메일 입니다."
		)

	except controllers.PasswordPatternError:
		raise HTTPException(
			status_code=400,
			detail="비밀번호는 8자 이상, 20자 이하이며, 대문자, 소문자, 숫자, 특수문자를 \
			각각 최소 1개 포함해야 합니다."
		)
    
	except controllers.PasswordAgainError:
		raise HTTPException(
			status_code=404,
			detail="비밀번호가 다릅니다."
		)
