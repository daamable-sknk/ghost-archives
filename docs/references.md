# 레퍼런스

ghost-archives 프로젝트 설계에 참고하는 외부 프로젝트.

## 1. Nemotron-Personas-Korea

- URL: https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea
- 성격: NVIDIA가 한국 인구통계(KOSIS, 대법원, 건보공단 등) 기반으로 합성한 100만 페르소나 데이터셋
- 라이선스: CC BY 4.0
- 구조: 26개 필드 (인구통계 + 7종 페르소나 텍스트)
- 생성: Gemma-4-31B-it + 확률적 그래프 모델(PGM)

### 참고 포인트
- **합성 데이터의 구조화**: 비정형 텍스트(페르소나 서술)와 정형 메타데이터(나이, 지역, 직업)를 하나의 스키마로 통합
- **분류 체계 설계**: 인구통계적 변수를 축으로 삼아 다양성을 확보하는 방식 — ghost-archives에서 '아카이브' 용례를 분류할 때 유사한 다축 접근 가능
- **규모와 재현성**: 데이터 생성 파이프라인을 공개하여 누구든 재현 가능

## 2. AI Readable Gazette KR

- URL: https://hosungseo.github.io/ai-readable-gazette-kr/
- GitHub: https://github.com/hosungseo/ai-readable-gazette-kr
- 성격: 대한민국 관보 PDF → Markdown 변환 + OCR 보정 파생 코퍼스
- 규모: 2020-2026 관보 약 13만 건

### 참고 포인트
- **"공개 ≠ 활용 가능"**: 관보는 이미 공개되어 있지만 PDF 안에 갇혀 기계가 읽지 못함 — ghost-archives도 '아카이브'라는 단어의 용례가 도처에 있지만 수집·구조화되지 않으면 분석 불가능하다는 동일한 문제의식
- **파이프라인 투명성**: 원천 → 변환 → 보정의 흐름을 문서화하고, 스크립트를 공개하여 과정 자체를 검증 가능하게 함
- **핵심 원칙 명시**: "원문 우선 / 과장보다 정확성 / 대시보드보다 신뢰 / 캠페인보다 아카이브" — 프로젝트의 태도를 선언하는 방식
- **보정 이력 관리**: v4~v7까지의 치환 규칙과 과보정 사고를 기록으로 남김 — 데이터 품질 관리의 모범

## 3. Nemotron-Personas-Korea Explorer

- URL: https://leejeonghwan.github.io/slowletter-pipeline/nemotron_personas_korea_explorer.html
- 성격: 위 데이터셋의 정적 사이트 탐색기 (GitHub Pages)

### 참고 포인트
- **정적 사이트에서의 데이터 탐색**: 서버 없이 GitHub Pages만으로 대시보드 + 브라우저 + 필터 검색 구현
- **UI 구성**: 통계 대시보드(분포 차트) → 개별 레코드 브라우저 → 조건 필터의 3단계 탐색 경로
- **ghost-archives 웹사이트에 직접 적용 가능한 패턴**: 현재 index.html이 있지만 데이터를 실제로 보여주는 기능이 없음 — 이 탐색기의 구조를 참고하여 카테고리별 필터, 소스별 분류, 시계열 뷰 구현 가능
