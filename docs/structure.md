# ghost-archives 프로젝트 구조

## 개요

'아카이브'라는 단어가 실제로 어디서, 어떻게 쓰이는지를 수집하고 분류하는 프로젝트.
기표는 같지만 기의가 분기하는 현상을 귀납적으로 분석하여 〈아카이브라는 이름의 유령〉 글의 논거를 구축한다.

- 사이트: https://ghost.meta-archives.xyz
- 저장소: https://github.com/daamable-sknk/ghost-archives
- 수동 수집: https://www.are.na/daehwan-jang/ghost-archive
- 상위 프로젝트: https://meta-archives.xyz

---

## 디렉토리 구조

```
ghost-archives/
├── CNAME                       # GitHub Pages 커스텀 도메인 (ghost.meta-archives.xyz)
├── README.md                   # 프로젝트 소개
├── requirements.txt            # Python 의존성
├── .gitignore
│
├── index.html                  # 메인 페이지 — 용례 목록, 필터, 통계
├── about.html                  # 프로젝트 소개 페이지
├── methodology.html            # 수집 방법론 페이지
├── assets/
│   └── style.css               # 공통 스타일시트
│
├── data/
│   ├── ghosts.json             # 전체 데이터 (병합본, 웹사이트가 읽는 파일)
│   └── sources/
│       ├── rss.json            # Google News RSS 수집 원본
│       ├── naver.json          # 네이버 뉴스 API 수집 원본
│       └── arena.json          # Are.na 수동 수집 (미구현)
│
├── scripts/
│   ├── collect.py              # 수집 스크립트 (RSS + Naver)
│   └── classify.py             # Gemini 기반 자동 분류 스크립트
│
├── docs/
│   ├── structure.md            # ← 이 문서
│   ├── plan.md                 # 작업 계획
│   └── references.md           # 외부 레퍼런스 분석
│
└── .github/
    └── workflows/
        └── collect.yml         # GitHub Actions — 매일 자동 수집
```

---

## 데이터 흐름

```
[수집]                          [저장]                    [분류]                  [표시]
Google News RSS ──┐
                  ├─ collect.py ──→ data/sources/*.json ──→ ghosts.json
Naver News API ───┘       │                                    │
                          │                                    ↓
                          │                              classify.py
                          │                              (Gemini 2.5 Flash)
                          │                                    │
                          ↓                                    ↓
                    GitHub Actions               ghosts.json (category 채워짐)
                    (매일 09:00 KST)                           │
                                                               ↓
Are.na (수동) ──→ arena.json ──────────────→               index.html
                    (미구현)                          (GitHub Pages로 서빙)
```

### 수집 (collect.py)

1. Google News RSS에서 "아카이브"/"archive" 키워드 검색
2. 네이버 뉴스 API에서 "아카이브"/"아카이빙" 검색
3. 각 소스별 JSON에 저장 (`data/sources/`)
4. URL 기반 중복 제거 후 `data/ghosts.json`으로 병합
5. GitHub Actions가 매일 자동 실행 → 커밋 & 푸시

### 분류 (classify.py)

1. `ghosts.json`에서 `category`가 null인 항목 추출
2. Gemini 2.5 Flash API로 제목 기반 분류
3. 7개 카테고리 중 하나 + `implied_meaning` 생성
4. 결과를 `ghosts.json`에 직접 반영
5. 현재 수동 실행 (자동화 미완)

---

## 데이터 스키마

### ghosts.json 최상위

```json
{
  "meta": {
    "title": "ghost-archive",
    "description": "'아카이브'라는 단어의 용례 수집",
    "last_updated": "2026-04-26T15:03:29+00:00",
    "total_count": 244,
    "reviewed_count": 0
  },
  "items": [...]
}
```

### 개별 항목

```json
{
  "id": "ghost-2026-04-26-a1b2c3d4",
  "source_type": "news",
  "source_url": "https://...",
  "source_title": "브랜드 아카이브 컬렉션 출시",
  "collected_at": "2026-04-26",
  "published_at": "2026-04-26",
  "keyword": "아카이브",
  "language": "ko",
  "auto_collected": true,
  "reviewed": false,
  "category": null,
  "implied_meaning": null,
  "note": null
}
```

### 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| id | string | `ghost-{날짜}-{URL 해시 8자리}` |
| source_type | string | `news` (향후 `sns`, `brand`, `academic` 등 확장) |
| source_url | string | 원문 URL |
| source_title | string | 제목 |
| collected_at | string | 수집일 (UTC) |
| published_at | string | 원문 발행일 |
| keyword | string | 매칭된 키워드 (아카이브, archive 등) |
| language | string | `ko` 또는 `en` |
| auto_collected | boolean | 자동 수집 여부 |
| reviewed | boolean | 수동 검토 완료 여부 |
| category | string\|null | 7개 분류 중 하나 |
| implied_meaning | string\|null | 이 맥락에서 '아카이브'의 실제 의미 (10자 이내) |
| note | string\|null | 메모 |

---

## 분류 체계

| 카테고리 | 설명 | 색상 |
|----------|------|------|
| 마케팅 | 브랜드 헤리티지, 굿즈, 컬렉션, 패션 | 빨강 |
| 감성 | 힙함, 구별짓기, 레트로, 추억, 향수 | 보라 |
| 큐레이션 | 선별, 플레이리스트, 콘텐츠 모음 | 노랑 |
| 시민 | 대항 기억, 사회운동, 커뮤니티 기록, 구술 | 초록 |
| 제도 | 공공기록, 기관, 도서관 | 회색 |
| 기술 | 백업, 버전관리, 소프트웨어 | 검정 |
| 예술 | 전시, 미술관, 영화, 음악, 창작 재료, 형식 실험 | 파랑 |

분류는 수집 과정에서 귀납적으로 조정한다.

---

## 인프라

### GitHub Pages

- 소스: `main` 브랜치 / `/ (root)`
- 커스텀 도메인: `ghost.meta-archives.xyz`
- DNS: 가비아 (meta-archives.xyz)
  - A 레코드 4개 → GitHub Pages IP
  - CNAME `www` → `daamable-sknk.github.io`
  - CNAME `ghost` → `daamable-sknk.github.io`

### GitHub Actions

- 워크플로: `.github/workflows/collect.yml`
- 스케줄: 매일 00:00 UTC (09:00 KST)
- 필요 시크릿: `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`
- 분류용 (미연동): `GEMINI_API_KEY`

### 외부 서비스

| 서비스 | 용도 | 비용 |
|--------|------|------|
| Google News RSS | 뉴스 수집 (한/영) | 무료 |
| Naver News API | 뉴스 수집 (한) | 무료 (일 25,000건) |
| Gemini API | 자동 분류 | 무료 티어 (분당 15건) |
| Are.na | 수동 수집 | 무료 |

---

## 웹사이트 구성

| 페이지 | 파일 | 내용 |
|--------|------|------|
| 목록 | index.html | 수집 데이터 목록, 소스/언어 필터, 통계 |
| 소개 | about.html | 프로젝트 배경, "왜 유령인가" |
| 방법론 | methodology.html | 수집 범위, 소스, 프로세스, 분류 체계, 스키마 |

프론트엔드는 순수 HTML/CSS/JS — 프레임워크 없음.
`data/ghosts.json`을 fetch하여 클라이언트에서 렌더링.

---

## 관련 프로젝트

- **본문**: 〈아카이브라는 이름의 유령〉 — meta-archives.xyz (예정)
- **수동 수집**: [Are.na ghost-archive](https://www.are.na/daehwan-jang/ghost-archive)
- **상위**: [meta-archives.xyz](https://meta-archives.xyz)
