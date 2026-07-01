from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from baseline import build_rag_chain

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI 앱 초기화 시점에 인덱싱 + RAG 체인 구성
    _, app.state.rag = build_rag_chain()
    yield

app = FastAPI(lifespan=lifespan)

class QueryRequest(BaseModel):
    symbol: str = ""
    context: str
    page_title: str
    question: str = ""

class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = []


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if req.symbol:
        question = f"${req.symbol}$이 ${req.context}$에서 사용됐습니다. 현재 페이지: {req.page_title}. 기호에 대해서 설명해주세요."
    else:
        question = req.question
    result = app.state.rag.invoke(question)
    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
        )