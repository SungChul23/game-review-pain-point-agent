from dotenv import load_dotenv
from graph import app
from games import GAMES

load_dotenv()

print("🎮 분석할 게임을 선택하세요")
for i, name in enumerate(GAMES.keys(), 1):
    print(f"  {i}. {name}")

# 선택
choice = int(input("\n번호 입력: ")) - 1
game_name = list(GAMES.keys())[choice]
game_info = GAMES[game_name]

print(f"\n✅ {game_name} 선택됨\n")

query = input("분석할 내용을 입력해주세요 (ex. 과금, 밸런스, 버그 등): ")

# ── 초기 State ─────────────────────────────────────
initial_state = {
    "game_name":       game_name,
    "package_name":    game_info["package_name"],
    "platforms":       [game_info["platform"]],
    "max_reviews":     3000,
    "top_n":           5,
    "reviews":         [],
    "neg_reviews":     [],
    "retry_count":     0,
    "collection_name": "",
    "pain_points":     [],
    "suggestions":     [],
    "report":          None,
    "error":           None,
    "messages":        [],
    "query":           query
}


config = {"configurable": {"thread_id": "compro-001"}}

# ── 실행 ───────────────────────────────────────────
print("🚀 Pain Point 에이전트 시작\n")

icons = {
    "fetch":      "📥",
    "filter":     "🔍",
    "embed":      "🧮",
    "cluster":    "🗂",
    "prioritize": "📊",
    "suggest":    "💡"
}

for event in app.stream(initial_state, config=config):
    node, output = list(event.items())[0]
    print(f"{icons.get(node, '⚙')} [{node}] 완료\n")

# ── 최종 결과 출력 ─────────────────────────────────
final = app.get_state(config).values

print("\n" + "="*50)
print("📋 Pain Point 우선순위")
print("="*50)
for i, pp in enumerate(final["pain_points"], 1):
    print(f"{i}. [{pp['category']}] {pp['summary']} | 점수: {pp['score']}")
    print(f"실제 유저 리뷰:")
    for review in pp.get("samples_review", []):
        print(f"  - {review}")

print("\n" + "="*50)
print("💡 개선 제안")
print("="*50)
for sg in final["suggestions"]:
    print(f"\n[{sg['pain_point_category']}] {sg['title']}")
    print(f"우선순위: {sg['priority']}/5")
    print(f"→ {sg['description']}")