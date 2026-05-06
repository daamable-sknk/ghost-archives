#!/usr/bin/env python3
"""이벤트 클러스터링 스크립트.

같은 카테고리 내에서 발행일 ±3일, 제목 유사도 50% 이상인 기사를 
같은 이벤트로 묶는다. Union-Find로 그룹 병합.
"""

import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
GHOSTS_PATH = BASE_DIR / "data" / "ghosts.json"

# 설정
DATE_WINDOW = 3  # 일
SIMILARITY_THRESHOLD = 0.4  # 자카드 유사도 임계값


def tokenize(title: str) -> set:
    """제목을 토큰 집합으로 변환. 한글/영문 단어 단위."""
    # 특수문자 제거, 소문자화
    title = re.sub(r"[^\w\s]", " ", title.lower())
    tokens = set(title.split())
    # 1글자 토큰 제거 (조사 등 노이즈)
    tokens = {t for t in tokens if len(t) > 1}
    return tokens


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return None


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1


def cluster():
    with open(GHOSTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["items"]

    # 카테고리별 그룹
    by_cat = defaultdict(list)
    for i, item in enumerate(items):
        cat = item.get("category") or "미분류"
        by_cat[cat].append(i)

    uf = UnionFind(len(items))

    # 각 카테고리 내에서 클러스터링
    for cat, indices in by_cat.items():
        # 날짜순 정렬
        indices_sorted = sorted(indices, key=lambda i: items[i].get("published_at") or "")

        # 토큰 캐시
        tokens = {i: tokenize(items[i].get("source_title", "")) for i in indices_sorted}

        # 슬라이딩 윈도우 비교
        for a_pos, a_idx in enumerate(indices_sorted):
            a_date = parse_date(items[a_idx].get("published_at"))
            if not a_date:
                continue

            for b_pos in range(a_pos + 1, len(indices_sorted)):
                b_idx = indices_sorted[b_pos]
                b_date = parse_date(items[b_idx].get("published_at"))
                if not b_date:
                    continue

                # 날짜 범위 초과하면 중단
                if (b_date - a_date).days > DATE_WINDOW:
                    break

                # 유사도 비교
                sim = jaccard(tokens[a_idx], tokens[b_idx])
                if sim >= SIMILARITY_THRESHOLD:
                    uf.union(a_idx, b_idx)

    # 클러스터 결과 집계
    clusters = defaultdict(list)
    for i in range(len(items)):
        root = uf.find(i)
        clusters[root].append(i)

    # event_id 부여
    event_counter = 0
    for root, members in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True):
        event_counter += 1
        event_id = f"evt-{event_counter:04d}"
        # 대표: 가장 빠른 날짜
        members_sorted = sorted(members, key=lambda i: items[i].get("published_at") or "")
        for i in members_sorted:
            items[i]["event_id"] = event_id
            items[i]["event_size"] = len(members)

    # 통계
    total_events = event_counter
    multi_events = sum(1 for members in clusters.values() if len(members) > 1)
    largest = max(len(m) for m in clusters.values())

    print(f"총 기사: {len(items)}")
    print(f"총 이벤트: {total_events}")
    print(f"복수 기사 이벤트: {multi_events}")
    print(f"최대 클러스터: {largest}건")
    print(f"단독 기사: {total_events - multi_events}")
    print()

    # 큰 클러스터 상위 10개 출력
    big_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    print("## 상위 이벤트 클러스터")
    for root, members in big_clusters:
        if len(members) < 2:
            break
        rep = min(members, key=lambda i: items[i].get("published_at") or "")
        print(f"  [{len(members)}건] {items[rep].get('category')} | {items[rep].get('source_title', '')[:50]}")

    # 저장
    data["meta"]["total_events"] = total_events
    with open(GHOSTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {GHOSTS_PATH}")


if __name__ == "__main__":
    cluster()
