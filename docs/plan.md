# ghost-archives 작업 계획

## 현황 (2026-05-06 기준)

- 수집: 803건 (Google News RSS + 네이버 뉴스), 전부 news 소스
- 분류: 720건 완료 / 83건 실패 (미분류)
- 웹사이트: ghost.meta-archives.xyz — HTTPS 라이브
- 자동화: GitHub Actions 매일 수집 가동 중, 분류는 수동 실행
- 모델: gemini-2.5-flash-lite (classify.py)

### 분류 결과 분포

| 카테고리 | 건수 | 비율 |
|---|---|---|
| 예술 | 234 | 32.5% |
| 제도 | 217 | 30.1% |
| 마케팅 | 88 | 12.2% |
| 감성 | 53 | 7.4% |
| 큐레이션 | 47 | 6.5% |
| 시민 | 47 | 6.5% |
| 기술 | 34 | 4.7% |
| 미분류 | 83 | — |

### 완료한 것

- [x] CNAME 도메인 변경 → ghost.meta-archives.xyz
- [x] DNS CNAME 레코드 추가 (가비아) + GitHub Pages 설정 + HTTPS
- [x] 전체 문서에서 Bluesky 참조 제거 (README, methodology, about, index)
- [x] 분류 체계 7개로 통일 (README, methodology.html, classify.py)
- [x] classify.py 모델 업데이트 (gemini-1.5-flash → 2.5-flash → 2.5-flash-lite)
- [x] classify.py 중간 저장 기능 추가 (10건마다)
- [x] 720건 자동 분류 실행 완료, 커밋 & 푸시
- [x] docs/ 폴더 생성 — structure.md, plan.md, references.md
- [x] .venv 환경 구성 (requests, feedparser)

---

## Phase 1: 데이터 품질 확보 ← 지금 여기

### 1-1. 분류 체계 검증
- [ ] 미분류 83건 원인 파악 및 재시도
- [ ] 분류 결과 샘플 검토 (정확도 체감 확인)
- [ ] 분류 체계 재검토 — 예술+제도가 62.6%로 편중, 카테고리 세분화 필요한지 판단
- [ ] 카테고리 간 경계 사례 정리
- [ ] `reviewed` 필드 정책 결정 — 자동 분류 = reviewed인지, 수동 검토만 reviewed인지

### 1-2. 데이터 파이프라인 정비
- [ ] .venv을 .gitignore에 추가
- [ ] classify.log를 .gitignore에 추가
- [ ] sources/ → ghosts.json 병합 흐름 재확인
- [ ] 중복 제거 로직 점검
- [ ] 수집 로그/이력 관리 (날짜별 수집 건수)
- [ ] GitHub Actions에 분류 단계 추가 검토 (GEMINI_API_KEY 시크릿 필요)

### 1-3. 수집 소스 확장

#### Are.na 자동 동기화 (우선)
- [ ] collect.py에 Are.na API 연동 추가
- [ ] Are.na ghost-archive 채널의 블록을 arena.json으로 자동 가져오기
- [ ] 인스타그램, X/Twitter 등 수동 수집은 Are.na에 URL 저장 → 자동 동기화로 ghosts.json 반영
- [ ] source_type을 블록 출처에 따라 구분 (sns, brand, exhibition 등)

#### SNS 직접 수집 (검토)

| 플랫폼 | API | 키워드 검색 | 현실성 | 비고 |
|---|---|---|---|---|
| Bluesky | 무료 공개 | 가능 | ✓ | 이전 구현 코드 재활용 가능 |
| Reddit | 무료 | 가능 | ✓ | r/korea 등 서브레딧에서 "archive" 검색 |
| YouTube | 무료 | 가능 | △ | 영상 제목/설명에서 "아카이브" 검색 |
| X/Twitter | 유료 ($200/월~) | 가능 | ✗ | 비용 대비 효용 낮음 |
| Instagram | 공식 API 없음 | 불가 | ✗ | Are.na 수동 수집이 유일한 방법 |
| Mastodon | 무료 공개 | 가능 | △ | 한국어 사용자 적음 |

#### 수집 경로 정리

```
[자동 수집]
  Google News RSS ──→ rss.json
  Naver News API ──→ naver.json
  (Bluesky API) ──→ bluesky.json     ← 재도입 검토
  (Reddit API) ──→ reddit.json       ← 추가 검토

[수동 → 자동 동기화]
  Instagram ──→ Are.na ──→ arena.json
  X/Twitter ──→ Are.na ──→ arena.json
  브랜드/전시 ──→ Are.na ──→ arena.json

  모든 sources/*.json ──→ ghosts.json (병합)
```

#### 학술
- [ ] Google Scholar Alerts 연동 검토 (RSS 가능 여부)

---

## Phase 2: 웹사이트 — 탐색 가능한 뷰어

참고: nemotron explorer의 정적 사이트 탐색 패턴

### 2-1. 데이터 렌더링 개선
- [x] 대시보드 페이지 (dashboard.html) — 파이프라인 상태 + 카테고리 분포 차트 + 주간 수집 추이 (Chart.js)
- [x] index.html "검토됨" → "분류됨" (category 기반 카운트)로 변경
- [ ] 카테고리별 색상 태그 (7색 매핑) — 목록 페이지에 적용
- [ ] implied_meaning 표시
- [ ] 시계열 뷰 (수집일/발행일 기준)

### 2-2. 필터 및 탐색
- [ ] 카테고리 필터 (7개)
- [ ] 언어 필터 (ko/en) — 기존 구현됨
- [ ] 검색 (제목 텍스트)
- [ ] 소스 타입 필터 (소스 다양화 이후)

### 2-3. 통계 대시보드
- [x] 카테고리별 분포 차트 (dashboard.html)
- [x] 시간에 따른 수집량 추이 (주간, dashboard.html)
- [ ] 언어별 분포 차트

---

## Phase 3: 분석과 글쓰기 지원

### 3-1. 분류 체계 정교화
- [ ] implied_meaning 필드 패턴 분석
- [ ] 카테고리별 대표 사례 큐레이션
- [ ] 통계적 근거 정리 (카테고리 비율, 시간 추이 등)

### 3-2. 본문 연결
- [ ] 〈아카이브라는 이름의 유령〉 글의 논거로 사용할 데이터 선별
- [ ] ghost-archives 데이터를 meta-archives.xyz에서 인용하는 구조

---

## Phase 4: 프로젝트 문서화

참고: ai-readable-gazette-kr의 원칙 명시, 보정 이력 관리 방식

### 4-1. 방법론 문서 보강
- [ ] methodology.html — 수집·분류·검증 파이프라인 상세 기술
- [ ] 분류 기준 변경 이력 기록
- [ ] 한계와 편향 명시 (뉴스 편중, 자동 분류 오류율 등)

### 4-2. 프로젝트 원칙
- [ ] ghost-archives의 태도 선언
  - 예: "수집은 증거 확보다 / 분류는 해석의 시작이다 / 아카이브라는 이름 자체가 분석 대상이다"

---

## 데이터 규모 대응

현재 803건(~500KB). 모든 데이터는 GitHub 레포 `data/` 폴더에 JSON으로 저장.

### 단계별 대응

| 규모 | 시점(추정) | 문제 | 대응 |
|---|---|---|---|
| ~5,000건 (~3MB) | 6개월 내 | 없음 | 현행 유지 |
| ~10,000건 (~7MB) | 1년 내 | 브라우저에서 ghosts.json 전체 로딩 느려짐 | 월별/연도별 JSON 분할 + 인덱스 파일 도입 |
| ~30,000건 (~20MB) | 2-3년 | git 이력 비대화 (.git 폴더) | sources/ 원본은 월별 아카이빙 후 truncate, 또는 git-lfs 전환 검토 |
| 10만건+ | 3년+ | GitHub Pages 정적 사이트 한계 | SQLite + Datasette 또는 별도 DB 이전 검토 |

### 비용 위험

| 항목 | 현재 | 위험 시점 |
|---|---|---|
| Google News RSS | 무료 | 없음 (공개 RSS) |
| 네이버 뉴스 API | 무료 (일 25,000건) | 없음 |
| Gemini 분류 | 무료 티어 (분당 15건) | 대량 분류 시 rate limit. 유료 전환 또는 배치 간격 조정 |
| GitHub Actions | 무료 (월 2,000분) | 수집만이면 충분. 분류까지 자동화하면 모니터링 필요 |
| GitHub 레포 | 무료 (권장 1GB) | 수년간 문제 없음 |

---

## 우선순위

1. **Phase 1-1** — 분류 결과 검증. 미분류 83건 처리, 편중 분석.
2. **Phase 1-3 Are.na** — 수동 수집 파이프라인 완성 (인스타 등 SNS → Are.na → ghosts.json).
3. **Phase 2-1** — 웹사이트에 카테고리 색상·필터 추가.
4. **Phase 1-2** — 파이프라인 안정화 (Actions에 분류 연동).
5. 나머지는 순차적으로.
