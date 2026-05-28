from dotenv import load_dotenv
from google_play_scraper import reviews, Sort
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from state import AgentState

load_dotenv()

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
embedding = HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")


def fetch_reviews_node(state: AgentState) -> dict:
    package = state["package_name"]
    max_count = state.get("max_reviews", 200)

    # 최신순 + 관련도순 조합
    result_new, _ = reviews(
        package, lang="ko", country="kr",
        sort=Sort.NEWEST, count=max_count // 2
    )
    result_rel, _ = reviews(
        package, lang="ko", country="kr",
        sort=Sort.MOST_RELEVANT, count=max_count // 2
    )

    # 중복 제거
    all_reviews = {r["reviewId"]: r for r in result_new + result_rel}
    raw = [
        {
            "text": r["content"],
            "rating": r["score"],
            "date": str(r["at"]),
            "platform": "google_play"
        }
        for r in all_reviews.values() if r.get("content")
    ]

    print(f"[fetch] 수집 완료: {len(raw)}개")
    return {
        "reviews": raw,
        "retry_count": state.get("retry_count", 0) + 1
    }


def filter_negative_reviews_node(state: AgentState) -> dict:
    reviews = state["reviews"]
    
    neg = [
        r['text'] for r in reviews
        if r["rating"] <= 3 and len(r['text']) >= 10  # 별점 3 이하 + 텍스트 길이 20자 이상
    ]


    print(f"[filter] 부정 리뷰 필터링 완료: {len(neg)}개")
    return {"neg_reviews": neg}

## 크로마 db 저장
def embed_and_store_node(state: AgentState) -> dict:
    neg_reviews = state["neg_reviews"]
    game_name = state["package_name"].replace (".", "-")
    collection_name = game_name.replace(" ", "_").lower()

    # Document로 변환
    docs = [
        Document(
            page_content=text,
            metadata={"game": game_name, "platform": "google_play"}
        )
        for text in neg_reviews
    ]

    # 기존 컬렉션 있으면 삭제 후 재저장
    import chromadb
    client = chromadb.PersistentClient(path="./data/chroma")
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
    return {}


def cluster_pain_points_node(state: AgentState) -> dict:
    game_name = state["game_name"]
    collection_name = state["package_name"].replace(".", "_")

    db = Chroma(
        embedding_function=embedding,
        collection_name=collection_name,
        persist_directory="./data/chroma"
    )

    ## MMR 로 다양한 리뷰 샘플링

    results = db.max_marginal_relevance_search(
        query="게임 불만 문제점",
        k=20,
        fetch_k=100
    )
    sample_text = "\n".join([f"- {doc.page_content}" for doc in results])

        # LLM으로 Pain Point 추출
    response = llm.invoke([HumanMessage(content=f"""
다음은 {game_name} 게임의 부정 리뷰들이에요.
카테고리별로 Pain Point를 추출해서 아래 JSON 형식으로 답해주세요.
카테고리: 성능/UI/과금/밸런스/콘텐츠/버그/기타

[
  {{
    "category": "카테고리명",
    "summary": "한 줄 요약",
    "detail": "구체적인 내용",
    "frequency": 언급 리뷰 수,
    "severity": 심각도 1.0~5.0
  }}
]

JSON만 출력하세요. 다른 텍스트 없이.

리뷰:
{sample_text}
""")])

    import json
    pain_points = json.loads(response.content)
    print(f"[cluster] Pain Point {len(pain_points)}개 추출")
    return {"pain_points": pain_points}

##노드 5 — 우선순위 계산
def prioritize_node(state: AgentState) -> dict:
    pain_points = state["pain_points"]
    total = len(state["neg_reviews"]) or 1

    for pp in pain_points:
        freq_score = pp["frequency"] / total # 언급 비율
        severity_score = pp["severity"] / 5.0 # 심각도 정규화
        pp["score"] = round(freq_score * 0.6 + severity_score * 0.4, 3)

    ranked = sorted(pain_points, key=lambda x: x["score"], reverse=True)

    print(f"[prioritize] 우선순위 정렬 완료")

    for i, pp in enumerate(ranked, 1):
        print(f"  {i}. [{pp['category']}] {pp['summary']} | 점수: {pp['score']}")
    
    return {"pain_points": ranked}

## 노드 6 솔루션 제안

def generate_suggestions_node(state: AgentState) -> dict:
    import json
    
    game_name = state["game_name"]
    top_n = state.get("top_n", 5)
    top_pps = state["pain_points"][:top_n]  # 상위 N개만

    suggestions = []
    for pp in top_pps:
        response = llm.invoke([HumanMessage(content=f"""
게임 기획자 관점에서 아래 Pain Point에 대한 개선안을 JSON으로 답해주세요.

게임: {game_name}
Pain Point: {json.dumps(pp, ensure_ascii=False)}

아래 형식으로 JSON만 출력하세요.
{{
    "title": "개선안 제목",
    "description": "구체적인 개선 방법 3문장 이상",
    "expected_impact": "기대 효과",
    "difficulty": "하/중/상",
    "priority": 1~5 숫자
}}
""")])
        
        suggestion = json.loads(response.content)
        suggestion["pain_point_category"] = pp["category"]
        suggestions.append(suggestion)
        print(f"[suggest] [{pp['category']}] 완료")

    return {"suggestions": suggestions}