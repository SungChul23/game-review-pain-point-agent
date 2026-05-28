from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    # 입력
    game_name:    str           # 게임 이름
    package_name: str           # 구글 플레이 패키지명
    platforms:    List[str]     # ["google_play"] 또는 ["google_play", "app_store"]
    max_reviews:  int           # 수집할 리뷰 수

    # 수집 단계
    reviews:      List[dict]    # 원본 리뷰 전체
    neg_reviews:  List[str]     # 부정 리뷰만 필터
    retry_count:  int           # 재수집 횟수

    # 분석 단계
    pain_points:  List[dict]    # 추출된 Pain Point
    top_n:        int           # 상위 몇 개 제안 생성할지

    # 생성 단계
    suggestions:  List[dict]    # 개선 제안
    report:       Optional[str] # 최종 보고서

    # 메타
    error:        Optional[str]
    messages:     Annotated[List[BaseMessage], add_messages]