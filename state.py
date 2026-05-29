from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    # ── 입력 ───────────────────────────────────────
    game_name:       str            # 게임 이름 (표시용)
    package_name:    str            # 구글 플레이 패키지명
    platforms:       List[str]      # ["google_play"] or ["google_play", "app_store"]
    max_reviews:     int            # 수집할 리뷰 수

    # ── 수집 단계 ──────────────────────────────────
    reviews:         List[dict]     # 원본 리뷰 전체
    neg_reviews:     List[str]      # 부정 리뷰 텍스트만
    retry_count:     int            # 재수집 횟수 (무한루프 방지)

    # ── 임베딩 단계 ────────────────────────────────
    collection_name: str            # Chroma 컬렉션 이름 (노드 간 공유)

    # ── 분석 단계 ──────────────────────────────────
    pain_points:     List[dict]     # 추출된 Pain Point 목록
    top_n:           int            # 개선 제안 생성할 상위 N개
    query:           str  # 사용자 질의 

    # ── 생성 단계 ──────────────────────────────────
    suggestions:     List[dict]     # 개선 제안 목록
    report:          Optional[str]  # 최종 마크다운 보고서

    # ── 메타 ───────────────────────────────────────
    error:           Optional[str]
    messages:        Annotated[List[BaseMessage], add_messages]  # LLM 대화 누적