import chromadb
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from nodes import (
    fetch_reviews_node,
    filter_negative_node,
    embed_and_store_node,
    cluster_pain_points_node,
    prioritize_node,
    generate_suggestions_node,
    skip_to_cluster_node
)

load_dotenv()


# ── 조건 함수 1: DB 존재 여부 확인 ────────────────
def route_after_start(state: AgentState) -> str:
    """Chroma에 이미 데이터 있으면 크롤링 스킵"""
    collection_name = state["package_name"].replace(".", "_")

    client   = chromadb.PersistentClient(path="./data/chroma")
    existing = [c.name for c in client.list_collections()]

    if collection_name in existing:
        collection = client.get_collection(collection_name)
        if collection.count() > 0:
            print(f"[start] 기존 DB 발견 ({collection.count()}개) — 크롤링 스킵")
            return "skip"

    print("[start] DB 없음 — 크롤링 시작")
    return "crawl"


# ── 조건 함수 2: 부정 리뷰 수 확인 ───────────────
def route_after_filter(state: AgentState) -> str:
    """부정 리뷰 수 + 재시도 횟수로 다음 경로 결정"""
    if state["retry_count"] >= 3:
        print("[경고] 최대 재시도 초과 — 있는 데이터로 진행")
        return "proceed"
    if len(state["neg_reviews"]) < 10:
        print(f"[재시도] 부정 리뷰 {len(state['neg_reviews'])}개 부족 — 재수집")
        return "refetch"
    return "proceed"


# ── 그래프 조립 ────────────────────────────────────
def build_graph():
    g = StateGraph(AgentState)

    # 노드 등록
    g.add_node("fetch",      fetch_reviews_node)
    g.add_node("filter",     filter_negative_node)
    g.add_node("embed",      embed_and_store_node)
    g.add_node("cluster",    cluster_pain_points_node)
    g.add_node("prioritize", prioritize_node)
    g.add_node("suggest",    generate_suggestions_node)
    g.add_node("skip",       skip_to_cluster_node)  # DB 있을 때 cluster로 바로 가는 노드

    # 시작 조건부 엣지 (DB 있으면 스킵)
    g.add_conditional_edges(
        START,
        route_after_start,
        {
            "crawl": "fetch",    # DB 없음 → 크롤링부터
            "skip":  "skip",  # DB 있음 → 바로 분석
        }
    )

    # 고정 엣지
    g.add_edge("fetch",      "filter")
    g.add_edge("embed",      "cluster")
    g.add_edge("cluster",    "prioritize")
    g.add_edge("prioritize", "suggest")
    g.add_edge("suggest",    END)
    g.add_edge("skip",       "cluster")  # DB 있을 때 바로 cluster로

    # 재수집 조건부 엣지
    g.add_conditional_edges(
        "filter",
        route_after_filter,
        {
            "proceed": "embed",   # 충분 → 임베딩으로
            "refetch": "fetch",   # 부족 → 재수집 루프
        }
    )

    return g.compile(checkpointer=MemorySaver())


app = build_graph()