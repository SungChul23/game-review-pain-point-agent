# 🎮 Game Review Pain Point Agent

LangGraph 기반 게임 리뷰 자동 분석 에이전트

구글 플레이스토어 게임 리뷰를 자동 수집하고, 유저 Pain Point를 추출하여 AI 기반 개선 제안을 생성하는 파이프라인 구축

---

## 📌 프로젝트 개요 및 목표

게임 서비스 운영에서 유저 불만을 빠르게 파악하고 개선 방향을 제시하는 것
이 프로젝트는 LangGraph 에이전트를 활용해 리뷰 수집부터 개선 제안까지 자동화 목표

---

## 🏗 아키텍처

```
START
  ↓
fetch_reviews        # 구글 플레이 리뷰 수집
  ↓
filter_negative      # 부정 리뷰 필터 (별점 2 이하)
  ↓ (부족하면 재수집)
embed_and_store      # 임베딩 → Chroma DB 저장
  ↓
cluster_pain_points  # MMR 검색 + LLM Pain Point 추출
  ↓
prioritize           # 빈도 × 심각도 우선순위 계산
  ↓
generate_suggestions # LLM 개선 제안 생성
  ↓
END
```

---

## 🛠 기술 스택

| 역할 | 기술 |
|---|---|
| 에이전트 프레임워크 | LangGraph |
| LLM | GPT-3.5 Turbo (OpenAI) |
| 임베딩 | jhgan/ko-sroberta-multitask (HuggingFace) |
| 벡터 DB | Chroma DB |
| 리뷰 수집 | google-play-scraper |
| 언어 | Python 3.11 |

---

## 📁 프로젝트 구조

```
pain_point_agent/
├── state.py       # AgentState 정의
├── nodes.py       # 6개 노드 함수
├── graph.py       # StateGraph 조립
├── main.py        # 실행 진입점
├── .env           # API 키 (git 제외)
└── requirements.txt
```



---

## 📊 출력 예시

```
✅ [fetch] 완료 — 리뷰 100개 수집
✅ [filter] 완료 — 부정 리뷰 35개
✅ [embed] 완료 — Chroma 저장
✅ [cluster] 완료 — Pain Point 7개 추출
✅ [prioritize] 완료 — 우선순위 정렬
✅ [suggest] 완료 — 개선 제안 생성

📋 Pain Point 우선순위
1. [버그] 게임 내 버그 발생 | 점수: 0.469
2. [과금] 과금이 너무 많이 필요함 | 점수: 0.402
3. [성능] 게임이 느리고 버벅거림 | 점수: 0.335

💡 개선 제안
[버그] 버그 수정 및 품질 향상
→ 우선적으로 버그를 신속하게 수정하고...
```

---

## 🚀 향후 계획

### 1단계 — FastAPI 백엔드 연동

LangGraph 에이전트를 API 서버로 감싸서 외부에서 호출 가능하게 만들 예정

```
프론트 (웹 UI)
      ↓ HTTP 요청
 FastAPI 서버        ← API 키 서버에서 관리
      ↓
LangGraph 에이전트
      ↓
  Chroma DB
```

```python
# 예정 엔드포인트
POST /analyze           # 게임 분석 요청
GET  /games             # 분석된 게임 목록
GET  /result/{game_id}  # 분석 결과 조회
```

### 2단계 — 웹 클라이언트 연동

자연어로 게임 Pain Point를 질문하고 결과를 확인하는 웹 UI 연동 예정.

```
유저: "[게임 명] 성능 문제 알려줘"
        ↓
에이전트가 자동으로 분석
        ↓
Pain Point + 개선 제안 반환
```

- 게임이 DB에 없으면 자동 크롤링 후 분석
- 게임이 있으면 기존 Chroma DB에서 바로 검색

### 3단계 — 기능 고도화 (예정)

- [ ] 앱스토어 리뷰 수집 추가
- [ ] LLM 게임 도메인 지식 부족 → game_knowledge DB + Tavily 웹서치 노드 추가
- [ ] 별점 필터 정확도 부족 → 한국어 감성 분석 모델 추가 (snunlp/KR-FinBert-SC)

---

## 📝 학습 목적

- LangGraph State / Node / Edge 개념 실습
- LangChain LCEL 파이프라인 구성
- Chroma DB 벡터 검색 활용
- HuggingFace 한국어 임베딩 모델 활용
- FastAPI 백엔드 연동 (예정)