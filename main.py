from dotenv import load_dotenv
from graph import app

load_dotenv()

# 초기 State 설정
initial_state = {
    "game_name":    "컴투스프로야구v26",
    "package_name": "com.com2us.futurecpb.android.google.global.normal",
    "platforms":    ["google_play"],
    "max_reviews":  3000,
    "top_n":        5,
    "reviews":      [],
    "neg_reviews":  [],
    "retry_count":  0,
    "pain_points":  [],
    "suggestions":  [],
    "report":       None,
    "error":        None,
    "messages":     []
}

config = {"configurable": {"thread_id": "compro-001"}}

# 실행
print("🚀 Pain Point 에이전트 시작\n")
for event in app.stream(initial_state, config=config):
    node, output = list(event.items())[0]
    print(f"✅ [{node}] 완료")

# 최종 결과
final = app.get_state(config).values
print("\n📋 Pain Point 우선순위")
for i, pp in enumerate(final["pain_points"], 1):
    print(f"{i}. [{pp['category']}] {pp['summary']} | 점수: {pp['score']}")

print("\n💡 개선 제안")
for sg in final["suggestions"]:
    print(f"\n[{sg['pain_point_category']}] {sg['title']}")
    print(f"→ {sg['description'][:80]}...")