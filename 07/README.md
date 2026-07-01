# LaTeX 기호 Parser  
  
## 1. 서론  
  
### 1-1. 과제 주 기능  

<img width="376" height="157" alt="스크린샷 2026-07-01 오후 1 06 39" src="https://github.com/user-attachments/assets/124eb6ea-ceb9-416c-a838-2787a2cb02c9" />
  
  
파란 박스를 선택하여 식의 맥락을 파악하거나 식의 기호의 의미를 알 수 있고,  
세부적으로 빨간 박스를 고를 수도 있다.  
대답은 기호(혹은 단어) 자체의 의미를 말하거나, 기호가 어떤 맥락이나 역할을 가지고 있는지 말한다.  
이후 추가적인 질문은 보통의 챗봇처럼 이야기할 수 있다.  
  
### 1-2. 과제 전체 요약  
  
이번 과제는 **데이터를 불러와서 → LLM을 추가 내용으로 학습시키고  
→ 이를 토대로 답변을 생성하게 하는** 과정이었다.  
추가로 이를 **LangChain 구조로 연결하고 → LangSmith를 통해 평가하며  
→ FastAPI로 연동**하였다  
  
| 구분        | 수행한 내용                                                                                                        | 핵심 개념                            |  
| --------- | ------------------------------------------------------------------------------------------------------------- | -------------------------------- |  
| RAG       | LLM 연동, 학습 데이터 호출/청킹/임베딩/Chroma 인덱싱,<br>프롬프팅 후 알맞은 답변 생성의 흐름                                                  | 외부 지식 연동 흐름                      |  
| LangChain | TextLoader, RecursiveCharacterTextSplitter,<br>Embedding, ChatPromptTemplate, <br>RunnableParrallel 사용        | 통일된 RAG 스타일,<br>'\|'를 통한 LCEL 방식 |  
| LangSmith | 평가할 수 있는 질문 생성<br>1\.키워드 포함 확인 함수<br>2\. ChatPromptTemplate를 통한 답변 품질을 평가 프롬프트<br>이후 두 방식을 Evaluator에 연결 및 비교 | RAG 파이프라인 평가 흐름                  |  
| FastAPI   | RAG를 통한 LLM의 답변과 참고 문서를 반환하는 <br>간단한 API 서버 생성                                                                | FastAPI가 입력받고 반환하는 데이터 구조 파악     |  
  
---  
  
## 2. 과제 진행 흐름  
  
```text  
LangChain 퀘스트  
→ ChatModel 연동  
→ RAG 학습 데이터 전처리  
→ RAG 파이프라인 실행  
  
LangSmith 퀘스트  
→ 평가 질문-대답 생성  
→ Dataset 생성/연동 및 평가 질문-대답 연동  
→ 평가 함수 생성 및 평가  
  
FastAPI 퀘스트  
→ FastAPI 연동  
```  
  
---  
  
## 3. RAG 데이터 활용  
  
최종 목표에 도달하기까지의 여러 경우를 나열해보았다  
  
### 3-1. Wikipedia  
  
**사용 이유**:  
- 가장 최종의 목표.  
- 위키피디아에 검색 시 개념이나 기호 굉장히 일반적. 친절하지 않음  
  → 이 서비스의 필요성이 가장 높은 문서  
- 현재 기호에 대한 설명은 연동하는 LLM의 학습된 지식으로 해설  
  → Wikipedia 데이터 이용 시 자체 챗봇 연동 가능  
  
**현재 상황에선?**:  
- `WikipediaLoader` 존재 → 그러나 검색 키워드를 통해 입력. 직접 문서 선택 불가  
- 당장은 간단한 문서로 서비스의 작동 여부부터 확인  
- 이 서비스는 모르는 수학 개념을 검색창에 질문하는 서비스 X  
  → 특정 정의, 정리에 모르는 부분을 클릭하여 대응하는 Wikipedia 문서를 통해 챗봇 대답  
  
### 3-2. 원서 교재  
  
**사용 이유**:  
- 적지 않은 양의 정의/정리  
- 보통 서문에 필요한 기호 설명되어 있음  
- 모든 정의/정리 흐름이 다 유기적으로 연결됨  
- 정의/정리 설명이 가장 잘 되어 있음, 여러 원서를 통해 다양한 해석 포함 가능  
  
**현재 상황에선?**:  
- `PyPDFLoader` 등의 PDF를 읽어들이는 Loader가 안정적이지 않음  
- 원서 분량이 매우 큰데도 불구, 여러 원서 필요  
- PDF 양식이 복잡하며, 원서 별 PDF 양식이 다름  
  → 작동 여부 판별하기에 부적절  
  
### 3-3. md 파일 수업노트  
  
**사용 이유**:  
- 가장 간단한 양식이자 LLM이 학습하기에 가장 좋은 형식  
- LaTeX 기호 문법 그대로 담겨 있음  
  
**현재 상황에선?**:  
- 정의가 인용구로 되어 있어 청킹 간편  
- RAG 학습 양이 많지 않은 문제  
- RAG가 잘 작동되지 않더라도,  
  연동되는 LLM이 답변할 수 있어 작동 여부 판별하기에 가장 적절  
  → 그러나 기호 지식을 온전히 LLM에게 의존하므로 장기적인 문제 해결 필요성 존재  
  
---  
  
## 4. LangChain 활용  
  
LangChain 문법 사용을 통해 RAG의 흐름을 LCEL이라는 보편화된 형태로 파악할 수 있었다.  
  
### 4-1. ChatModel  
  
```python  
def build_llm():  
    return ChatGoogleGenerativeAI(  
        model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"),  
        google_api_key=os.getenv("GOOGLE_API_KEY"),  
    )  
  
# 자체 모델 사용 시 함수 내부에 넣을 문법  
# provider = os.getenv("LLM_PROVIDER", "google").lower()  
# print(f"LLM Provider: {provider}")  
# if provider == "custom":  
#    from model_custom import CustomTransformerLLM  
#    return CustomTransformerLLM()  
```  
  
- `ChatGoogleGenerativeAI`를 사용하여 Gemini 2.5 Flash 모델 사용  
  
### 4-2. RAG 학습 데이터 전처리  
  
```python  
def build_rag_chain():  
    md_paths = sorted(glob("md/**/*.md", recursive=True))  
    md_docs = []  
    for p in md_paths:  
        md_docs.extend(TextLoader(p, encoding="utf-8").load())  
  
    docs = md_docs  
    print(f"로딩된 Document 수: {len(docs)}")  
```  
  
- `glob`을 사용하여 작업 폴더 내의 md 파일 탐색  
  `recursvie=True`를 통해 추후 복잡한 폴더 경로 생성 시에도 탐색 가능  
- 탐색된 `md_paths`를 통해 `TextLoader`로 문서 로딩 후 `md_docs`에 추가  
  **중요사항**: TextLoader는 `metadata`의 `"source"`로 파일 경로가 남음.  
  이를 이용해 해당 서비스에서 모르는 개념에 대한 문서 접근할 수 있음.  
  Digital Garden 식의 서비스 구상 가능  
  
```python  
    splitter = RecursiveCharacterTextSplitter(  
        chunk_size=500,  
        chunk_overlap=50,  
        separators=["\n\n", "\n", " ", ""],  
        add_start_index=False,  
    )  
    split_docs = splitter.split_documents(docs)  
    print(f"분할된 chunk 수: {len(split_docs)}")  
```  
  
- `RecursiveCharacterTextSplitter`를 사용하여 구분자 우선순위 지정 가능  
  
```python  
    embeddings = GoogleGenerativeAIEmbeddings(  
        model="models/gemini-embedding-001",  
        google_api_key=os.getenv("GOOGLE_API_KEY"),  
    )  
    vectorstore = Chroma.from_documents(split_docs, embeddings)  
    print("인덱싱 완료")  
```  
  
- 임베딩은 `GoogleGenerativeAIEmbeddings` 이용  
- 일단은 작동 여부 판단이므로 `Chroma`를 통해 벡터DB 인-메모리 인덱싱.  
  
### 4-3. RAG 파이프라인  
  
```python  
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
```  
  
- 유사도 기반 `retriever` 사용  
- 프롬프트는 본래  
  ㄱ. 사용자가 기호 선택: 첫 질문 형태 고정 →  
  → 해당 질문을 받았다면 기호 자체가 의미하는 바 + 기호가 해당 정리/정의에 의미하는 바 설명  
  → 후자가 없다면 전자만 설명  
  ㄴ. 이후 사용자의 직접 질문: RAG를 통해 설명  
  → RAG 근거가 없다면 '주어진 자료에서 확인 불가'로 대답  
  의 방식으로 예외 처리 하려고 했으나,  
  프롬프트가 너무 복잡하고, 당장은 LLM을 연동하므로 '일반적인 수학 지식'으로 일축  
- 위키피디아 연동이나 자체 챗봇 연결 시 추가적인 프롬프트 필요할 수 있음  
  
```python  
def format_docs(docs):  
    return "\n\n".join(doc.page_content for doc in docs)  
  
# ...  
  
    llm = build_llm()  
  
    rag_chain = RunnableParallel(  
        answer={"context": retriever | format_docs, "question": RunnablePassthrough()}  
        | prompt | llm | StrOutputParser(),  
        sources=retriever | (lambda docs: [d.metadata["source"] for d in docs])  
    )  
```  
  
- 이동할 수 있는 링크 정보 가져오려면 일반적인 직렬 체인 구조로는 부족하다. `"source"`가 이어지지 않음  
  → `RunnableParallel`: metadata로 문서의 출처를 가져옴  
  
  
---  
  
## 5. LangSmith 활용  
  
평가할 수 있는 질문 생성하여 특정 방식들을 Evaluator에 넣고 비교  
  
### 5-1. 평가 질문-대답 생성  
  
```python  
EVAL_QUESTIONS = [  
    {  
        "question": "$\\sum$이 $\\sum_{i=1}^n x_i$에서 사용됐습니다. 현재 페이지: Def. Convergence in Distribution. 기호에 대해서 설명해주세요.",  
        "answer": "$\\sum$은 합산 기호로, 인덱스 $i$가 $1$부터 $n$까지 $x_i$를 모두 더하는 연산을 의미합니다.",  
    },  
    # ...  
]  
print(f"검증 질문 수: {len(EVAL_QUESTIONS)}")  
```  
  
두 가지 질문 형태 존재  
- 기호 선택 시: 정해진 문장 형태로 질문 생성됨  
  현재 페이지를 보여주어 맥락 파악이 가능하게 함  
- 기본 질문 시: 일반적인 RAG로 작동.  
  
### 5-2. Dataset 생성 및 평가 질문-대답 연동  
  
```python  
existing = [d for d in client.list_datasets(dataset_name=DATASET_NAME)]  
  
inputs  = [{"question": ex["question"]} for ex in EVAL_QUESTIONS]  
outputs = [{"answer":   ex["answer"]}   for ex in EVAL_QUESTIONS]  
  
if existing:  
    dataset = existing[0]  
    print(f"기존 Dataset 사용: {dataset.id}")  
else:  
    dataset = client.create_dataset(  
        dataset_name=DATASET_NAME,  
        description="RAG 답변 품질 평가용",  
    )  
    print(f"새 Dataset 생성: {dataset.id}")  
  
    client.create_examples(  
        dataset_id=dataset.id,  
        inputs=inputs,  
        outputs=outputs,  
    )  
    print(f"Example {len(EVAL_QUESTIONS)}건 추가 완료")  
  
loaded = client.read_dataset(dataset_name=DATASET_NAME)  
  
examples = list(client.list_examples(dataset_id=loaded.id))  
print(f"총 Example 수: {len(examples)}")  
  
for ex in examples[:3]:  
    print("Q:", ex.inputs["question"])  
    print("A:", ex.outputs["answer"] if ex.outputs else "(없음)")  
    print()  
```  
  
기존 dataset이 존재한다면 기존으로, 없다면 새로 생성하여  
`EVAL_QUESTIONS`을 `inputs`나 `outputs` 변수를 통해 연동  
  
### 5-3. 두 가지 평가 함수 생성  
  
```python  
llm, rag_chain = build_rag_chain()  
  
def target(inputs):  
    return {"answer": rag_chain.invoke(inputs["question"])["answer"]}  
  
def contains_expected_keyword(run, example):  
    pred = run.outputs.get("answer", "")  
    # answer 비었으면 빈 칸 넣어라  
    expected = example.outputs.get("answer", "")  
  
    keywords = [w for w in expected.split() if len(w) >= 2][:2]  
    hit = all(k in pred for k in keywords)  
    # 키워드를 뽑아서 그 키워드가 다 들어있으면 1점 줘라  
  
    return {  
        "key": "contains_expected_keyword",  
        "score": 1 if hit else 0,  
        "comment": f"필수 키워드 {keywords} 포함 여부",  
    }  
```  
  
두 글자 이상의 단어 중 앞의 두 개를 뽑아 키워드로 지정한 후,  
키워드가 있다는 가정 하에 hit 점수를 제공  
완전히 좋은 방식은 아니지만, 성능 비교에 적절할 것으로 판단  
  
```python  
JUDGE_PROMPT = ChatPromptTemplate.from_messages([  
    ("system",  
     "당신은 답변 품질을 평가하는 채점자입니다.\n"  
     "아래 기대 답변(reference)과 모델 답변(prediction)을 비교하고,\n"  
     "의미가 일치하면 1, 부분적으로만 일치하면 0.5, 무관하면 0을 점수로 매기세요.\n"  
     "응답은 반드시 첫 줄에 0/0.5/1 중 하나의 숫자만, 둘째 줄부터 짧은 이유를 적으세요."),  
    ("human",  
     "질문: {question}\n\n"  
     "기대 답변: {reference}\n\n"  
     "모델 답변: {prediction}"),  
])  
  
judge_chain = JUDGE_PROMPT | llm | StrOutputParser()  
  
def llm_judge(run, example):  
    reply = judge_chain.invoke({  
        "question": example.inputs["question"],  
        "reference": example.outputs["answer"],  
        "prediction": run.outputs["answer"],  
    })  
  
    first_line = reply.strip().splitlines()[0].strip()  
    try:  
        score = float(first_line)  
    except ValueError:  
        score = 0  
    return {  
        "key": "llm_judge_semantic_match",  
        "score": score,  
        "comment": reply,  
    }  
```  
  
LLM과 프롬프트를 이용해 LangChain을 만들어 가장 앞에 LLM이 판단한 점수 생성  
  
### 5-4. 두 방식으로 평가 후 결과 관찰  
  
```python  
result = evaluate(  
    target,  
    data=DATASET_NAME,  
    evaluators=[contains_expected_keyword, llm_judge],  
    # 두 방식을 사용해서 비교하자. 전자가 좀 더 부정확하고 빠른 친구  
    experiment_prefix="v1-baseline",  
)  
```  
  
`evaluate`를 이용해 두 가지 evaluator 함수 대입  
  
<img width="1624" height="273" alt="스크린샷 2026-06-30 오후 4 37 30" src="https://github.com/user-attachments/assets/28d36484-390a-4caa-8b1c-e6762af699c2" />  
  
LLM을 사용한 방식은 전부 hit 했으나,  
키워드 방식은 기호 선택 방식에서 hit 하지 못 하였다.  
아마 기호 선택 질문은 기호 문서 자체가 없다보니 키워드 선택 측면에서 불리했을 수 있다.  

---
  
## 6. FastAPI 연동  
  
```python  
@asynccontextmanager  
async def lifespan(app: FastAPI):  
    _, app.state.rag = build_rag_chain()  
    yield  
  
app = FastAPI(lifespan=lifespan)  
```  
  
- FastAPI 앱 초기화 시점에 인덱싱 후, RAG 체인 구성  
  
```python  
class QueryRequest(BaseModel):  
    symbol: str = ""  
    context: str = ""  
    page_title: str = ""  
    question: str = ""  
  
class QueryResponse(BaseModel):  
    answer: str = ""  
    sources: list[str] = []  
```  
  
**QueryRequest**  
- symbol: 청킹된 것 중 사용자가 고른 것을 받아들임  
  아마 LaTeX(혹은 KaTeX)의 형태가 될 것  
- context: 가장 처음의 예시에서 파란 박스에 해당. 수식의 맥락을 봄  
- page_title: 해당 기호가 어느 식에서 사용되는지 알려줌  
첫 질문의 이후의 질문은 주로 question이 남게 될 것이다.  
  
**QueryResponse**  
- sources: 대답의 page_title을 알려줌. 링크로 향할 수 있게 함  
  사실 이런 링크랑 수식을 볼 수 있단 것 자체가 그런 get 같은걸 더 만들긴 해야 할 듯  
  
```python  
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
```  
  
- `QueryRequest`를 받아서 `req.symbol`이 존재한다면 `question`이 특정 형태가 될 수 있도록 함  
  기호 질문이든, 그냥 질문이든 보통의 RAG가 질문 받듯이 받게하기로 결정함  
- 원활한 링크 이동을 위해 `sources`를 꼭 남기자  
  
---  
  
## 7. 앞으로 만들고자 하는 것  
  
사용자가 개념 검색  
→ 위키피디아 API로 원본 마크업 가져옴  
→ LaTeX 추출 후 자체 사이트에서 KaTeX으로 렌더링  
  (위키피디아 그대로 보여주는 게 아니라 우리가 직접 렌더링)  
→ 수식/텍스트 어디든 클릭 가능  
→ 클릭 시 RAG 작동:  
- 기호 자체의 일반적 의미 검색  
- 이 문서 맥락에서의 의미 검색  
→ 답변 + sources (관련 위키피디아 페이지 링크) 반환  
→ sources 링크 클릭 → 다시 위키피디아 API → 자체 렌더링 반복  
  (digital garden 구조)  
  
백엔드 자체는 문법적이나 기능적으로 더 완성도 있게 하면 생각보다 거의 마무리 단계인데,  
원하던 기능을 곰곰히 생각해보니 위키피디아의 데이터를 가꾸고,  
프론트엔드를 구현해야하는 것에 가깝다는 것을 알게 되었다.  
  
---  
  
## 8. 최종 회고  
  
RAG라는 기능을 이용해 흥미로운 프로젝트를 진행하고자 했지만,  
이러한 LLM 응용 애플리케이션의 전체 흐름, 더해서 서비스와 그 서비스의 평가 흐름까지 알 수 있는 경험이였다.  
  
솔직히 RAG를 설계하고 응용하는 것 자체도 어려운 일이였지만, md 파일을 청킹하고 RAG 식으로 LLM에게 보여주어 답변을 얻는 과정을 살펴보면서 실제 배포되는 서비스에서 현재 상용화된 AI 연결의 원리를 알게 되었고, 이번 프로젝트의 최종 목적지처럼 여러 응용을 떠올릴 수도 있었다.  
  
아직 LangGraph 등의 마이그레이션을 해본 것도 아니고, 서비스의 구색을 맞추기 위해선 여러 추가적인 기능이 필요하겠지만, RAG를 연결하고, 대답에 대한 평가를 하고, FastAPI를 연동시키는 흐름을 직접 구현함으로써 실제 서비스에서 마주치는 업무에 대한 이해를 얻었다. 조금 더 여러 데이터를 불러오고, 해당하는 프론트엔드까지 구현함으로써 LaTeX 수학 설명 서비스로 배포할 때까지 열심히 개선해나갈 것이다.  
