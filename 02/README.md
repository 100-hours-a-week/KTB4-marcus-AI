# (1) main.py  
  
```python  
from fastapi import FastAPI, HTTPException  
from routers.post import router as post_router  
from routers.login import router as login_router  
  
app = FastAPI()  
  
app.include_router(post_router)  
app.include_router(login_router)  
```  
FastAPI 객체를 만들고, router를 잇는다!  
  
&nbsp;
# (2) models.py  
  
```python  
from pydantic import BaseModel  
class UserCheck(BaseModel): # 유저 정보  
    user_id: str  
    pwd: str  
  
  
class PostCreate(BaseModel): # 포스트 작성 시 정보  
    check: UserCheck  
    nickName: str  
    title: str  
    content: str  
  
class CommentCreate(BaseModel): # 댓글 작성 시 정보  
    check: UserCheck  
    nickName: str  
    content: str  
```  
BaseModel로 정의된 애들 여기에 집어넣는다!  
  
&nbsp;
# (3) login.py, post.py  
  
```python  
router = APIRouter(prefix="/posts", tags=["posts"])  
  
con_user = sqlite3.connect("users.db")  
cur_user = con_user.cursor()  
cur_user.execute("CREATE TABLE IF NOT EXISTS users(ID, pwd, nickName)")  
con_user.commit()  
  
con_comment = sqlite3.connect("comments.db")  
cur_comment = con_comment.cursor()  
cur_comment.execute("CREATE TABLE IF NOT EXISTS comments(ID, nickName, content, likes, \  
date, post_num)")  
con_comment.commit()  
```  
router를 APIRouter를 통해 생성한다.  
디렉토리에 따라서 `prefix`를 바꿀 수 있다  
`CREATE TABLE`을 이 파일에서 하는데, `IF NOT EXISTS`가 없으면 매번 에러가 났다  
  
```python  
con_post = sqlite3.connect("posts.db")  
cur_post = con_post.cursor()  
cur_post.execute("CREATE TABLE IF NOT EXISTS posts(ID, nickName, title, content, likes, \  
comments, views, date, post_num INTEGER PRIMARY KEY)")  
con_post.commit()  
```  
{LLM} 단, `cur_post` 같은 경우,  
`post_num`이 자동으로 추가되게 `INTERGER PRIMARY KEY`를 추가했다  
DB 명령어에서 `MAX`를 써서 계속 숫자를 추가하는 경우 오류가 많이 생긴다고 한다  
  
```python  
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
```  
그 외의 모든 router 명령어는 위와 같이 진행된다  
`commit()` 명령어를 넣어야 DB에 반영할 수 있었고,  
`global`로 호출하지 않으면 제대로 변수를 못 찾는 문제가 있었다  
  
&nbsp;
# (4) controllers.py  
  
## def1. login_checker  
  
>사용자 인증 과정이 실질적으로 담겨있는 함수다  
>로그인 창을 위한 것이 아닌, 게시물 작성, 수정, 삭제 등의 작업에서 인증하는 용도다  
  
### (받는 것)  
  
**data**: 유저 정보 class, **cur_user**: 유저 DB cursor  
  
### (함수 과정)  
  
ㄱ. data에 맞는 사람을 cur_user가 가리키는 users DB에서 찾아서 뽑아낸다  
~~ㄴ~~. 정보가 없으면 IDPasswordIncorrectError()  
ㄷ. 있다면 return한다  
  
### (비고)  
  
일단 로그인이라는 구색은 맞추고 싶고, 인증 없이도 뭔가 방법이 있겠다 싶었는데,  
막상 '로그인 상태'라는 것을 만드려니 엄청 막막했다.  
실제로는 접속해있다는 토큰 같은게 필요한가 보다.  
  
그래서 정말 원시적인 방법이지만, 우회할 방법을 생각해봤는데,  
평소에 게시물을 보는 등의 행위는 가능하지만,  
게시물을 작성하거나 댓글을 쓰거나 게시물 수정, 삭제 등은 **전부 아이디, 비번을 요구하는 것**  
그 **작업들에 대해 이 함수를 호출하는 것이다**  

&nbsp;
  
## def2. signup_controller  
  
>사용자 회원가입 과정이 실질적으로 담겨있는 함수다  
  
### (받는 것)  
  
**data**: 유저 정보 class, **pwd_again**: 비밀번호 확인,  
**nickName**: 본인이 등록할 닉네임, **cur_user**: 유저 DB cursor  
  
  
### (함수 과정)  
  
~~ㄱ~~. data.user_id가 이메일 형식이 아니라면 EmailPatternError()를 낸다  
ㄴ. data에 맞는 사람이 이미 cur_user가 가리키는 users DB에 있는지 확인한다  
~~ㄷ~~. 있다면 IDAlreadyExists()를 낸다  
~~ㄹ~~. data에 적은 비밀번호가 비밀번호 형식에 맞지 않다면 PasswordPatternError()를 낸다  
~~ㅁ~~. data에 적은 비밀번호와 pwd_again이 다르다면 PasswordAgainError()를 낸다  
ㅂ. 이 모든걸 통과한다면 users DB에 회원 정보를 등록한다  
ㅅ. 회원가입 성공 메시지를 return 한다  
  
### (비고)  
  
과제 1에서 배운 정규식 문법을 이용했는데,  
`EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.com$")`  
`PWD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\~\!\@\#\$\%\^\&\*\|\'\"\;\:\₩\\\?]).{8,20}$")`  
이메일 패턴은 쉬웠지만, 비밀번호 패턴이 정말 골때렸다  
  
커뮤니티 예시에서의 비밀번호 패턴은 소문자, 대문자, 숫자, 특수문자가 하나 이상 들어있는 상태로  
비밀번호가 8~20자리여야 했는데,  
이를 위해 맨 앞에서 각 기호가 하나 이상 존재해야 하는 후방 탐색 조건을 넣었다  
  
본래 소문자, 대문자, 숫자, 특수문자들로 8~20자를 만들고, 전방 탐색 조건을 넣으려고 했으나,  
그러면 소문자, 대문자, 숫자, 특수문자를 제외한 다른 기호를 넣을 수가 없는 문제가 발생한다.  
{LLM} 그래서 해당 `PWD_PATTERN`은 내 머릿 속에서 나온건 아니다  

<img width="680" height="582" alt="스크린샷 2026-05-25 오후 10 57 44" src="https://github.com/user-attachments/assets/ef5665e6-2811-4661-ab76-a34ff55b6a3d" />
<img width="656" height="292" alt="스크린샷 2026-05-25 오후 10 57 53" src="https://github.com/user-attachments/assets/437a702f-93bc-4fb6-838e-708a969aae9f" />
  
**한창 이 프로젝트를 처음할 때 login이나 회원가입을 할 때 비밀번호도 return 했었다**  
중간중간에 LLM에게 코드 평가를 맡겼는데 LLM이 그 지점에서 기겁했었다  

&nbsp;  
## def3. post_outside_contorller  
  
>페이지에 따른 게시물을 보여주는 과정이 실질적으로 담겨있는 함수다  
  
### (받는 것)  
  
**page_num**: 현재 페이지를 알려준다, **cur_post**: 게시물 DB cursor  
  
### (함수 과정)  
  
ㄱ. page_num을 통해 페이지에 따라 건너뛸 게시물의 수인 pass_num을 구한다  
ㄴ. cur_post가 가리키는 posts DB에서  
post_num을 내림차순으로 하고, pass_num으로부터 10개의 게시물을 가져온다  
ㄷ. 해당 게시물들의 정보를 담은 dictionary들을 담은 posts_list를 만든다  
ㄹ. posts_list와 page_num을 return한다  
  
### (비고)  
  
페이지도 구현하고 싶은 욕심에 만든 함수다.  
그 과정에서 많은 시행착오가 있었으나, 이에 맞는 SQL 명령어를 찾았다  
다만 구글 검색하다가 AI가 알려준걸로 써서 좀 찜찜하긴 하다  
  
dictionary에 넣은 것들은 커뮤니티 예시에서 보이는 것을 다 적어봤다  
물론 포스트 번호인 post_num 정도는 더 넣고.  

&nbsp;
## def4. post_inside_controller  
  
>게시물 내부를 보여주는 과정이 실질적으로 담겨있는 함수다  
  
### (받는 것)  
  
**post_num**: 현재 페이지를 보여준다, **cur_post**: 게시물 DB cursor,  
**cur_comment**: 댓글 DB cursor  
  
### (함수 과정)  
  
ㄱ. post_num을 통해 posts DB의 게시물을 찾는다  
~~ㄴ~~. 해당 게시물이 없다면 NoPostError()를 낸다  
ㄷ. posts DB의 post_num으로 특정된 게시물의 조회수를 1 올린다  
ㄹ. post_dict로 해당 게시물의 정보를 가져온다  
ㅁ. post_num을 통해 해당 post의 댓글을 comments DB에서 찾는다  
ㅂ. 해당 게시물들의 정보를 담은 dictionary들을 담은 comments_list를 만든다  
ㅅ. post_dict와 coments_list를 return한다  
  
### (비고)  
  
댓글을 다른 디렉토리로 넣어야 하나 고민했지만,  
일단 예시 커뮤니티에선 댓글이 같이 보이므로,  
댓글 쓰는 것만 다른 디렉토리에 넣기로 했다  
&nbsp;
  
## def5. like_controller  
  
>좋아요를 하는 과정이 실질적으로 담겨있는 함수다  
  
### (받는 것)  
  
**post_num**: 현재 페이지를 보여준다, **cur_post**: 게시물 DB cursor  
  
### (함수 과정)  
  
ㄱ. post_num으로 특정된 게시물에 대해 posts DB에서 likes를 올린다  
ㄴ. 좋아요 성공 메시지를 return한다  
  
### (비고)  
  
**현재 문제가 많은 함수다**  
**로그인 인증이 따로 구현되어 있지 않아서 무한으로 좋아요를 누르는걸 막을 방법이 없다**  

&nbsp;
  
## def6. comment_controller  
  
>댓글 작성 과정이 실질적으로 담겨있는 함수다  
  
### (받는 것)  
  
**data**: 댓글 작성 class, **post_num**: 현재 페이지를 보여준다,  
**cur_post**: 게시물 DB cursor, **cur_comment**: 댓글 DB cursor  
  
### (함수 과정)  
  
ㄱ. 작성한 로그인 정보가 cur_user가 가리키는 users DB에 있는지 확인한다  
~~ㄴ~~. 작성한 댓글 내용이 없다면 EmptyComment()를 낸다 ~~지금 보니 Error를 안 붙였다~~  
ㄷ. 현재 날짜를 구하고, 형식에 맞춘다  
ㄹ. 댓글 정보를 comments DB에 맞게 집어넣는다  
ㅁ. 댓글 작성 성공 메시지를 return 한다  
  
### (비고)  
  
날짜 문법은 아무래도 인터넷에 그대로 찾아서 이용했다  
`... VALUES (?, ?, ?, ?, ?, ?)", (data.check.user_id, ... , 0, ...))`  
{LLM} `VALUES()` 부분 안에 `?` 말고 상수 값 정도는 집어넣어도 된다고 생각했으나,  
LLM의 말로는 이러면 치명적인 오류가 생길 수 있다고 한다  
`?` 개수와 tuple의 개수가 맞는게 SQLite한테 좋다고 한다  

<img width="684" height="658" alt="스크린샷 2026-05-25 오후 11 18 02" src="https://github.com/user-attachments/assets/bc599a26-df07-4f39-be88-2b2e425b3458" />

<img width="662" height="292" alt="스크린샷 2026-05-25 오후 11 18 10" src="https://github.com/user-attachments/assets/59bdbd83-c3c6-42d9-862d-3638bdc5b4e5" />

  
&nbsp;
## def7. summary_controller  
  
>게시물 요약 과정이 실질적으로 담겨있는 함수다  
  
### (받는 것)  
  
**post_num**: 현재 페이지를 보여준다, **cur_post**: 게시물 DB cursor  
  
### (함수 과정)  
  
ㄱ. post_num에 맞는 게시물을 cur_post가 가리키는 posts DB에서 가져온다  
ㄴ. ollama를 url로 가져오고, 메시지 형식을 json의 형태로 고정시킨 뒤, 메시지 양식을 만든다  
`"role": "system"`으로 ollama에게 프롬프트를 건네주고,  
`"role": "user"`로 게시물을 넣는다  
ㄷ. httpx를 통해 Ollama의 API로부터 답변을 받는 시도를 한다  
~~ㄹ~~. 연결 자체가 안 된다면 AIOfflineError()를 낸다  
~~ㅁ~~. 제대로 된 답변을 받지 못한다면 AIBadCodeError()를 낸다  
ㅂ. 제대로 받는데 성공했다면, 수많은 정보 중 답변 메시지만 꺼내서 return한다  
  
### (비고)  
  
`"stream": False`로 했는데, 이게 선택형 위클리 챌린지에 나올 정도로 어려운 과정인데,  
이걸 `True`로 하는 정도의 일이 아닐 것 같아 일단 `False`로 했다  
  
답변을 받는 과정에서 `try` 방식을 최대한 피하고 싶었지만 쓰게 되었는데,  
httpx로부터 답변을 못 받는 방식이 너무 많아서  
`try` 방식과 `if response.status_code != 200:` 방식을 같이 쓰는게 최선이였다  

<img width="678" height="340" alt="스크린샷 2026-05-25 오후 11 35 22" src="https://github.com/user-attachments/assets/6d6d0e3b-aeae-47af-9347-d17ce3207323" />

<img width="680" height="315" alt="스크린샷 2026-05-25 오후 11 35 30" src="https://github.com/user-attachments/assets/74073b4b-23d3-4d92-809b-7ee32cc427bb" />

  
&nbsp;
## def8. revise_controller  
  
>게시물 수정 과정이 실질적으로 담겨있는 함수다  
  
### (받는 것)  
  
**data**: 포스트 생성 정보 class, **post_num**: 현재 페이지를 보여준다,  
**cur_user**: 유저 DB cursor, **cur_post**: 게시물 DB cursor  
  
### (함수 과정)  
  
ㄱ. 작성한 로그인 정보가 cur_user가 가리키는 users DB에 있는지 확인한다  
~~ㄴ~~. data 안에 게시물 제목이 20자를 넘긴다면 PostNamePatternError()를 낸다  
~~ㄷ~~. 게시물 제목이나 내용이 없다면 EmptyPost()를 낸다  
ㄹ. post_num에 맞는 게시물을 cur_post가 가리키는 posts DB에서 찾아 UPDATE한다  
ㅁ. 게시물 수정 성공 메시지를 return한다  

<img width="682" height="665" alt="스크린샷 2026-05-25 오후 11 19 54" src="https://github.com/user-attachments/assets/1d9ee29d-0bea-4338-9399-3da584a9248b" />

<img width="675" height="285" alt="스크린샷 2026-05-25 오후 11 20 00" src="https://github.com/user-attachments/assets/9bf9b732-aa0d-42a5-a402-8a47807ea79c" />

<img width="679" height="270" alt="스크린샷 2026-05-25 오후 11 20 29" src="https://github.com/user-attachments/assets/677b152e-9861-4767-b74d-dfdf11d7ccfd" />

  
&nbsp;
  
## def9. delete controller  
  
>게시물 삭제 과정이 실질적으로 담겨있는 함수다  
  
### (받는 것)  
  
**data**: 포스트 생성 정보 class, **post_num**: 현재 페이지를 보여준다,  
**cur_user**: 유저 DB cursor, **cur_post**: 게시물 DB cursor  
  
### (함수 과정)  
  
ㄱ. 작성한 로그인 정보가 cur_user가 가리키는 users DB에 있는지 확인한다  
ㄴ. post_num에 맞는 게시물을 cur_post가 가리키는 posts DB에서 찾아 DELETE한다  
ㄷ. 게시물 삭제 성공 메시지를 return한다  
  
### (비고)  
  
아마 post_num이 중간에 끼어있는 경우는 그냥 그 post_num만 DB에 비어있을 것 같은데,  
맨 끝 post_num을 삭제하면 어떻게 될지 궁금하긴 하다  

<img width="678" height="245" alt="스크린샷 2026-05-25 오후 11 36 43" src="https://github.com/user-attachments/assets/001a25f3-3c8a-494e-a24f-0a87ac469ce7" />

<img width="676" height="292" alt="스크린샷 2026-05-25 오후 11 36 50" src="https://github.com/user-attachments/assets/34f9c90f-c7dd-4085-bb9a-41e0487529cd" />

  
&nbsp;
## def10. publish_controller  
  
>게시물 생성 과정이 실질적으로 담겨있는 함수다  
  
### (받는 것)  
  
**data**: 포스트 생성 정보 class,  
**cur_user**: 유저 DB cursor, **cur_post**: 게시물 DB cursor  
  
### (함수 과정)  
  
ㄱ. 작성한 로그인 정보가 cur_user가 가리키는 users DB에 있는지 확인한다  
~~ㄴ~~. data 안에 게시물 제목이 20자를 넘긴다면 PostNamePatternError()를 낸다  
~~ㄷ~~. 게시물 제목이나 내용이 없다면 EmptyPost()를 낸다  
ㄹ. 게시물 생성 날짜를 찾는다  
ㅁ. cur_post가 가리키는 posts DB에 새로 등록한다  
ㅂ. 게시물 생성 성공 메시지를 return한다  
  
### (비고)  
  
이때 INSERT 시 post_num을 MAX 등으로 만들어서 하면  
SQL 상에서 MAX를 못 찾는 문제가 생길 수 있다  
따라서 posts DB 자체를 INSERT 시 post_num이 자동으로 1씩 추가하게 하여  
이 문제를 해결했다  

<img width="681" height="569" alt="스크린샷 2026-05-25 오후 11 14 21" src="https://github.com/user-attachments/assets/8df2a23b-01e6-48a6-93f3-814069e5d70b" />

<img width="657" height="292" alt="스크린샷 2026-05-25 오후 11 14 29" src="https://github.com/user-attachments/assets/94f18dc2-2304-4ec7-950d-483977257ccc" />
