#!/usr/bin/env python3
"""implied_meaning 분석 스크립트.

카테고리별 implied_meaning 빈도를 집계하고,
유사 표현 그룹을 식별하기 위한 1차 분석.
"""

import json
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
GHOSTS_PATH = BASE_DIR / "data" / "ghosts.json"
OUTPUT_PATH = BASE_DIR / "data" / "analysis_meanings.json"


def analyze():
    with open(GHOSTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data["items"]
    by_cat = {}

    for item in items:
        cat = item.get("category")
        im = item.get("implied_meaning")
        if cat and im:
            by_cat.setdefault(cat, []).append(im)

    result = {}
    for cat in sorted(by_cat.keys()):
        counts = Counter(by_cat[cat])
        unique = len(counts)
        total = len(by_cat[cat])
        result[cat] = {
            "total": total,
            "unique_meanings": unique,
            "diversity_ratio": round(unique / total, 2),
            "top_meanings": [
                {"meaning": m, "count": c}
                for m, c in counts.most_common(20)
            ],
        }

    # 전체 요약
    summary = {
        "total_classified": sum(r["total"] for r in result.values()),
        "total_unique_meanings": sum(r["unique_meanings"] for r in result.values()),
        "categories": result,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 콘솔 출력
    print(f"총 분류 건수: {summary['total_classified']}")
    print(f"고유 implied_meaning 수: {summary['total_unique_meanings']}")
    print()

    for cat, info in result.items():
        print(f"## {cat} — {info['total']}건, 고유 {info['unique_meanings']}개 (다양성 {info['diversity_ratio']})")
        for item in info["top_meanings"][:5]:
            print(f"   {item['meaning']}: {item['count']}")
        print()


if __name__ == "__main__":
    analyze()
