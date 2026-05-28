from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import AgentState
from nodes import (
    fetch_reviews_node,
    filter_negative_reviews_node,
    embed_and_store_node,
    cluster_pain_points_node,
    prioritize_node,
    generate_suggestions_node
)

load_dotenv()

# ── 조건 함수 ──────────────────────────────────
def route_after_filter(state: AgentState) -> str:
    if state["retry_count"] >= 3:
        print("[경고] 최대 재시도 초과 — 그냥 진행")
        return "proceed"
    if len(state["neg_reviews"]) < 10:
        print(f"[재시도] 부정 리뷰 {len(state['neg_reviews'])}개 — 재수집")
        return "refetch"
    return "proceed"

# ── 그래프 조립 ────────────────────────────────
def build_graph():
    g = StateGraph(AgentState)

    # 노드 등록
    g.add_node("fetch",      fetch_reviews_node)
    g.add_node("filter",     filter_negative_reviews_node)
    g.add_node("embed",      embed_and_store_node)
    g.add_node("cluster",    cluster_pain_points_node)
    g.add_node("prioritize", prioritize_node)
    g.add_node("suggest",    generate_suggestions_node)

    # 고정 엣지
    g.add_edge(START,        "fetch")
    g.add_edge("fetch",      "filter")
    g.add_edge("embed",      "cluster")
    g.add_edge("cluster",    "prioritize")
    g.add_edge("prioritize", "suggest")
    g.add_edge("suggest",    END)

    # 조건부 엣지 (재시도 루프)
    g.add_conditional_edges(
        "filter",
        route_after_filter,
        {
            "proceed": "embed",   # 충분 → 임베딩
            "refetch": "fetch",   # 부족 → 재수집
        }
    )

    return g.compile(checkpointer=MemorySaver())

app = build_graph()