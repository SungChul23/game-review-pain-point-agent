# games.py — 분석 가능한 게임 목록

GAMES = {
    "서머너즈워": {
        "package_name": "com.com2us.smon.normal.freefull.google.kr.android.common",
        "platform": "google_play"
    },
    "컴투스프로야구2026": {
        "package_name": "com.com2us.probaseball3d.normal.freefull.google.global.android.common",
        "platform": "google_play"
    },  
    "컴투스프로야구v26": {
        "package_name": "com.com2us.futurecpb.android.google.global.normal",
        "platform": "google_play",
        "domain_knowledge": """
        [게임 장르] 모바일 야구 매니지먼트
        [핵심 시스템]
        - 선수카드: 일반/시즌/임펙트/시그니처/골든글러브/국가대표 등급
        - 스카우트: 픽업 스카우트(특정 선수 확률 UP) / 일반 스카우트 / 우정 스카우트
        - 리그: 정규리그 / 포스트시즌 / 챔피언십
        - 훈련: 타격/투구/수비/체력 훈련으로 선수 능력치 향상
        - 강화: 선수카드 합성으로 등급 강화
        - 구단 운영: 선수 영입/방출, 라인업 구성
        - PVP: 실시간 대전 / 리그 순위전
        - 시즌 이벤트: 한정 선수카드, 시즌 미션
        """
    },
    "컴투스프로야구매니저LIVE2026": {
        "package_name": "com.com2us.kbomanager.normal2.freefull.google.global.android.common",
        "platform": "google_play"
    },
    "MLB9이닝스26": {
        "package_name": "com.com2us.ninepb3d.normal.freefull.google.global.android.common",
        "platform": "google_play"
    },
    "MLB9이닝스라이벌26": {
        "package_name": "com.com2us.futuremlb.android.google.global.normal",
        "platform": "google_play"
    },
    "버디크러시": {
        "package_name": "com.com2us.birdiecrush.normal.freefull.google.global.android.common",
        "platform": "google_play"
    },
    "아이모": {
        "package_name": "com.com2us.imo.normal.freefull.google.global.android.common",
        "platform": "google_play"
    },
    "미니게임천국": {
        "package_name": "com.com2us.minigame.android.google.global.normal",
        "platform": "google_play"
    },
}