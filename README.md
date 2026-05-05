# ghost-archive

'아카이브'라는 단어의 용례를 수집하고 분류하는 프로젝트

## About

하나의 단어가 유령처럼 떠돌고 있다—아카이브라는 이름의 단어가.

이 프로젝트는 '아카이브'라는 단어가 실제로 어디서, 어떻게 소비되는지를 수집한다. 기표는 같지만 기의가 분기하는 현상을 귀납적으로 분석하여, 〈아카이브라는 이름의 유령〉 글의 논거를 구축한다.

→ [ghost.meta-archives.xyz](https://ghost.meta-archives.xyz)

## 수집 범위

- **언어**: 한국어, 영어
- **소스**: 뉴스, SNS, 브랜드, 전시, 학술
- **방식**: 링크만 (스크린샷 X)

## 수집 방법

### 자동 수집 (GitHub Actions, 매일)

| 소스 | 방법 |
|------|------|
| 뉴스 (한/영) | Google News RSS |
| 뉴스 (한) | Naver News API |

### 수동 수집 (Are.na)

| 소스 | 방법 |
|------|------|
| Instagram | → [Are.na ghost-archive](https://www.are.na/daehwan-jang/ghost-archive) |
| X/Twitter | → Are.na |
| 브랜드/전시 | → Are.na |

## 구조

```
ghost-archive/
├── index.html              # 메인 페이지 (용례 목록)
├── about.html              # 프로젝트 설명
├── methodology.html        # 방법론
├── data/
│   ├── ghosts.json         # 전체 데이터 (자동+수동 병합)
│   └── sources/
│       ├── rss.json        # Google News RSS 자동 수집
│       ├── naver.json      # Naver News API 자동 수집
│       └── arena.json      # Are.na 수동 수집
├── scripts/
│   └── collect.py          # 수집 스크립트
├── .github/
│   └── workflows/
│       └── collect.yml     # GitHub Actions
└── assets/
    └── style.css
```

## 데이터 스키마

```json
{
  "id": "ghost-2026-04-26-001",
  "source_type": "news",
  "source_url": "https://...",
  "source_title": "브랜드 아카이브 컬렉션 출시",
  "collected_at": "2026-04-26",
  "keyword": "아카이브",
  "language": "ko",
  "auto_collected": true,
  "reviewed": false,
  "category": null,
  "implied_meaning": null,
  "note": null
}
```

## 분류 체계

| 카테고리 | 설명 | 색상 |
|----------|------|------|
| 마케팅 아카이브 | 브랜드 헤리티지, 굿즈, 컬렉션, 패션 | 빨강 |
| 감성 아카이브 | 힙함, 구별짓기, 레트로, 추억, 향수 | 보라 |
| 큐레이션 아카이브 | 선별, 플레이리스트, 콘텐츠 모음 | 노랑 |
| 시민 아카이브 | 대항 기억, 사회운동, 커뮤니티 기록, 구술 | 초록 |
| 제도 아카이브 | 공공기록, 기관, 도서관 | 회색 |
| 기술 아카이브 | 백업, 버전관리, 소프트웨어 | 검정 |
| 예술 아카이브 | 전시, 미술관, 영화, 음악, 창작 재료, 형식 실험 | 파랑 |

*분류는 수집 과정에서 귀납적으로 조정*

## 연결

- **본문**: [아카이브라는 이름의 유령](https://meta-archives.xyz/posts/the-ghost-called-archive/) (예정)
- **수동 수집**: [Are.na ghost-archive](https://www.are.na/daehwan-jang/ghost-archive)
- **상위 프로젝트**: [meta-archives.xyz](https://meta-archives.xyz)

## 라이선스

콘텐츠: CC BY 4.0  
코드: MIT
