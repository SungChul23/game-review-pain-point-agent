import json
import chromadb
from dotenv import load_dotenv
from google_play_scraper import reviews, Sort
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from state import AgentState
from transformers import pipeline

load_dotenv()

llm       = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embedding = HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")
sentiment_analyzer = pipeline("text-classification", model="daekeun-ml/koelectra-small-v3-nsmc") 
# 감정 분석을 위한 파이프라인


# ══════════════════════════════════════════════════
# 노드 1: 리뷰 수집
# ════════════════════════════════════════════════
def fetch_reviews_node(state: AgentState) -> dict:
    package   = state["package_name"]
    max_count = state.get("max_reviews", 200)

    # 최신순 + 관련도순 조합으로 다양한 리뷰 확보
    result_new, _ = reviews(
        package, lang="ko", country="kr",
        sort=Sort.NEWEST,       count=max_count // 2
    )
    result_rel, _ = reviews(
        package, lang="ko", country="kr",
        sort=Sort.MOST_RELEVANT, count=max_count // 2
    )

    # reviewId 기준 중복 제거
    all_reviews = {r["reviewId"]: r for r in result_new + result_rel}
    raw = [
        {
            "text":     r["content"],
            "rating":   r["score"],
            "date":     str(r["at"]),
            "platform": "google_play"
        }
        for r in all_reviews.values() if r.get("content")
    ]

    print(f"[fetch] 수집 완료: {len(raw)}개")
    return {
        "reviews":     raw,
        "retry_count": state.get("retry_count", 0) + 1
    }


# ══════════════════════════════════════════════════
# 노드 2: 부정 리뷰 필터 + 감정분석
# ══════════════════════════════════════════════════
def filter_negative_node(state: AgentState) -> dict:
    all_reviews = state["reviews"]

    neg_reviews = []
    for r in all_reviews:
        text = r["text"]

        if r["rating"] <= 1 and len(r["text"]) >= 10:  # 평점 1 이하 + 10자 이상 → 부정 리뷰 후보
            neg_reviews.append(text)
            continue

        if r["rating"] == 2 and len(r["text"]) >= 10:  # 평점 2 + 10자 이상 → 감정 분석으로 판별
            result = sentiment_analyzer(text[:512])  # 긴 텍스트는 모델 입력 제한에 맞게 자르기
            if result[0]["label"] == "LABEL_0":  # LABEL_0이 부정 클래스라고 가정
                neg_reviews.append(text)

    print(f"[filter] 부정 리뷰 필터링 완료: {len(neg_reviews)}개")
    return {"neg_reviews": neg_reviews} 


# ══════════════════════════════════════════════════
# 노드 3: 임베딩 & Chroma 저장
# ══════════════════════════════════════════════════
def embed_and_store_node(state: AgentState) -> dict:
    neg_reviews     = state["neg_reviews"]
    collection_name = state["package_name"].replace(".", "_")

    # Document 변환
    docs = [
        Document(
            page_content=text,
            metadata={
                "game":     state["game_name"],
                "platform": "google_play"
            }
        )
        for text in neg_reviews
    ]

    # 기존 컬렉션 삭제 후 재저장 (중복 방지)
    client   = chromadb.PersistentClient(path="./data/chroma")
    existing = [c.name for c in client.list_collections()]
    if collection_name in existing:
        client.delete_collection(collection_name)
        print(f"[embed] 기존 컬렉션 삭제: {collection_name}")

    db = Chroma.from_documents(
        docs,
        embedding=embedding,
        collection_name=collection_name,
        persist_directory="./data/chroma"
    )

    print(f"[embed] Chroma 저장 완료: {db._collection.count()}개")

    # collection_name을 State에 저장 → 다음 노드에서 재사용
    return {"collection_name": collection_name}


# ══════════════════════════════════════════════════
# 노드 4: Pain Point 클러스터링 (LCEL)
# ══════════════════════════════════════════════════
def cluster_pain_points_node(state: AgentState) -> dict:
    game_name       = state["game_name"]
    collection_name = state["collection_name"]  # embed 노드에서 넘겨받음

    # Chroma에서 불러오기
    db = Chroma(
        embedding_function=embedding,
        collection_name=collection_name,
        persist_directory="./data/chroma"
    )

    # MMR로 다양한 리뷰 30개 샘플링
    user_query = state.get("query", "게임 불만 문제점")  # 사용자 질의 추가 기본값으로
    sampled     = db.max_marginal_relevance_search(
        query = user_query,
        k=30, fetch_k=100, lambda_mult=0.4
    )
    sample_text = "\n".join([f"- {doc.page_content}" for doc in sampled])

    # LCEL 체인 구성
    prompt = ChatPromptTemplate.from_messages([
        ("system", """게임 리뷰 분석 전문가입니다.
{query} 관련 Pain Point에 집중해서 추출하세요.
{query}와 관련 없는 카테고리는 제외하세요.

반드시 아래 JSON 배열만 출력하세요. 다른 텍스트 없이.
[
  {{
    "category": "카테고리명",
    "summary": "한 줄 요약",
    "detail": "구체적인 내용",
    "frequency": 언급 리뷰 수(정수),
    "severity": 심각도 1.0~5.0,
    "samples_review": ["실제 예시 1", "실제 예시 2", "실제 예시 3"]
  }}
]"""),
        ("human", "게임: {game}\n\n리뷰:\n{reviews}")
    ])

    chain = prompt | llm | StrOutputParser()

    try:
        raw         = chain.invoke({"game": game_name, "query": state["query"], "reviews": sample_text})
        pain_points = json.loads(raw)
        print(f"[cluster] Pain Point {len(pain_points)}개 추출")
        return {"pain_points": pain_points}
    except json.JSONDecodeError:
        print("[cluster] JSON 파싱 실패 — 빈 리스트 반환")
        return {"pain_points": []}


# ══════════════════════════════════════════════════
# 노드 5: 우선순위 계산
# ══════════════════════════════════════════════════
def prioritize_node(state: AgentState) -> dict:
    pain_points = state["pain_points"]
    total       = len(state["neg_reviews"]) or 1

    for pp in pain_points:
        freq_ratio = pp["frequency"] / total   # 언급 비율
        severity   = pp["severity"]  / 5.0     # 심각도 정규화
        pp["score"] = round(freq_ratio * 0.6 + severity * 0.4, 3)

    ranked = sorted(pain_points, key=lambda x: x["score"], reverse=True)

    print("[prioritize] 우선순위 정렬 완료")
    for i, pp in enumerate(ranked, 1):
        print(f"  {i}. [{pp['category']}] {pp['summary']} | 점수: {pp['score']}")

    return {"pain_points": ranked}


# ══════════════════════════════════════════════════
# 노드 6: 개선 제안 생성 (LCEL)
# ══════════════════════════════════════════════════
def generate_suggestions_node(state: AgentState) -> dict:
    game_name = state["game_name"]
    top_n     = state.get("top_n", 5)
    top_pps   = state["pain_points"][:top_n]

    # LCEL 체인 구성
    prompt = ChatPromptTemplate.from_messages([
        ("system", """게임 기획자 관점에서 Pain Point에 대한 개선안을 제시하세요.

반드시 아래 JSON만 출력하세요. 다른 텍스트 없이.
{{
    "title": "개선안 제목",
    "description": "구체적인 개선 방법 3문장 이상",
    "expected_impact": "기대 효과",
    "priority": 1~5 숫자
}}"""),
        ("human", "게임: {game}\nPain Point: {pain_point}")
    ])

    chain = prompt | llm | StrOutputParser()

    suggestions = []
    for pp in top_pps:
        try:
            raw        = chain.invoke({
                "game":        game_name,
                "pain_point":  json.dumps(pp, ensure_ascii=False)
            })
            suggestion = json.loads(raw)
            suggestion["pain_point_category"] = pp["category"]
            suggestions.append(suggestion)
            print(f"[suggest] [{pp['category']}] 완료")
        except json.JSONDecodeError:
            print(f"[suggest] [{pp['category']}] JSON 파싱 실패 — 스킵")

    return {"suggestions": suggestions}

def skip_to_cluster_node(state: AgentState) -> dict:
    """DB 있을 때 collection_name만 세팅하고 cluster로 넘어가는 노드"""
    collection_name = state["package_name"].replace(".", "_")
    print(f"[skip] 기존 DB 사용: {collection_name}")
    return {"collection_name": collection_name}