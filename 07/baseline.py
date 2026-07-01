from glob import glob
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv
import os

load_dotenv()

# 인덱싱
print("문서 로딩 및 인덱싱 시작...")

def build_llm():
    # 개인 모델은 아직 아니야
    # provider = os.getenv("LLM_PROVIDER", "google").lower()
    # print(f"LLM Provider: {provider}")
    # if provider == "custom":
    #    from model_custom import TransformerLLM
    #    return TransformerLLM()
    return ChatGoogleGenerativeAI(
        model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

'''
# ========================이건 최종 목표=============================
from langchain_community_document_loaders import WikipediaLoader

topics = ["Linear Algebra", "Matrix", "Calculus", "Probability Theory", "Probability Distribution", "Real Analysis"]
docs = []


for topic in topics:
    loader = WikipediaLoader(query=topic, lang="en", load_max_docs=3)
    docs.extend(loader.load())
'''

'''
# ========================pdf는 생각보다 좋지 않았다=============================

from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("rag/학교확률론.pdf")
docs = loader.load()[10:25]

# 여기가 아마 문서 불러오는거. 이건 우리가 위키피디아에 맞춰서 할 것
'''

# ========================결국 내가 썼던 md 파일로=============================

def build_rag_chain():
    md_paths = sorted(glob("md/**/*.md", recursive=True))
    md_docs = []
    for p in md_paths:
        md_docs.extend(TextLoader(p, encoding="utf-8").load())

    docs = md_docs
    print(f"로딩된 Document 수: {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""],
        add_start_index=False,
    )
    split_docs = splitter.split_documents(docs)
    print(f"분할된 chunk 수: {len(split_docs)}")
    # 청킹 하고

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )
    vectorstore = Chroma.from_documents(split_docs, embeddings)
    print("인덱싱 완료")

    print("RAG 파이프라인 시작...")
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
        "당신은 수학 기호와 개념을 설명하는 전문가입니다. "
        "다음 문서를 근거로 사용자 질문에 답하세요. "
        "근거가 부족하면 일반적인 수학 지식으로 답하세요. \n\n"
        "{context}"),
        ("human", "{question}"),
    ])

    llm = build_llm()

    rag_chain = RunnableParallel(
        answer={"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt | llm | StrOutputParser(),
        sources=retriever | (lambda docs: [d.metadata["source"] for d in docs])
        # TextLoader로부터 온 docs는 metadata가 자동으로 남으니까 원본을 추적하고 링크를 줄 수 있겠지
    )

    print(rag_chain.invoke("확률론에서 Lotus가 무엇인가요?"))
    print("RAG 파이프라인 완료")

    return llm, rag_chain

if __name__ == "__main__":
    llm, rag_chain = build_rag_chain()