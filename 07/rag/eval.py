from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv

from langsmith.evaluation import evaluate
from langsmith import Client

from baseline import build_rag_chain

load_dotenv()

DATASET_NAME = "Math_RAG"

client = Client()

EVAL_QUESTIONS = [
    {
        "question": "$\\sum$이 $\\sum_{i=1}^n x_i$에서 사용됐습니다. 현재 페이지: Def. Convergence in Distribution. 기호에 대해서 설명해주세요.",
        "answer": "$\\sum$은 합산 기호로, 인덱스 $i$가 $1$부터 $n$까지 $x_i$를 모두 더하는 연산을 의미합니다.",
    },
    {
    "question": "Central Limit Theorem은 무엇을 의미하나요?",
    "answer": "iid 분포를 따르는 확률변수들의 합 $S_n$을 표준화한 $\\frac{S_n - n\\mu}{\\sigma\\sqrt{n}}$은 n이 무한대로 갈 때 분포가 무엇이든 관계없이 표준정규분포 $N(0,\\; 1)$로 분포 수렴합니다.",
    },
    {
        "question": "`$S_n$`이 `$S_n = \\sum X_n \\sim (n\\mu, n\\sigma^2)$`에서 사용됐습니다. 현재 페이지: Thm. Central Limit Theorem. 기호에 대해서 설명해주세요.",
        "answer": "$S_n$은 iid 분포를 따르는 확률변수 $X_1, \\cdots, X_n$의 합으로, 평균 $n\mu$, 분산 $n\\sigma^2$을 가집니다. CLT에서 이를 표준화하기 위한 출발점으로 사용됩니다.",
    },
    {
    "question": "왜 $\\int_{-\\infty}^\\infty e^{-x^2} dx$ 적분이 확률밀도함수에 쓰이나요?",
    "answer": "$\\int_{-\\infty}^\\infty e^{-t^2/2} dt = \\sqrt{2\\pi}$이므로, $e^{-t^2/2}$를 $\\sqrt{2\\pi}$로 나누면 전체 실수에서 적분값이 1이 됩니다. 이것이 정규분포 확률밀도함수의 정규화 상수 근거입니다.",
    },
    {
        "question": "`$\\int_{-\\infty}^\\infty$`이 `$\\int_{-\\infty}^\\infty e^{-x^2} dx = \\sqrt{\\pi}$`에서 사용됐습니다. 현재 페이지: Lem. 확률밀도함수에 쓰일 적분. 기호에 대해서 설명해주세요.",
        "answer": "$\\int_{-\\infty}^\\infty$는 실수 전체 구간에서의 적분을 의미합니다. 이 보조정리에서는 $e^{-x^2}$를 전체 실수에서 적분하면 $\\sqrt{\\pi}$가 됨을 극좌표 변환을 통해 보입니다.",
    },
]
print(f"검증 질문 수: {len(EVAL_QUESTIONS)}")

# 이건 나중에 채워넣자

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

result = evaluate(
    target,
    data=DATASET_NAME,
    evaluators=[contains_expected_keyword, llm_judge],
    # 두 방식을 사용해서 비교하자. 전자가 좀 더 부정확하고 빠른 친구
    experiment_prefix="v1-baseline",
)

print(result)
