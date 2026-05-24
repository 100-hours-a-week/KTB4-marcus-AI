from fastapi import FastAPI, HTTPException
from routers.post import router as post_router
from routers.login import router as login_router

app = FastAPI()

app.include_router(post_router)
app.include_router(login_router)