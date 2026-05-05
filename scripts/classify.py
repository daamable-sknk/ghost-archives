#!/usr/bin/env python3

import json
import os
import time
from pathlib import Path
import requests

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
GHOSTS_PATH = DATA_DIR / "ghosts.json"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

CATEGORIES = ["마케팅", "감성", "큐레이션", "시민", "제도", "기술", "예술"]

PROMPT_TEMPLATE = """다음은 '아카이브'라는 단어가 포함된 뉴스/소셜미디어 제목입니다.

제목: "{title}"

1. category: 다음 중 하나만 선택
   - 마케팅 (브랜드 헤리티지, 컬렉션, 빈티지, 패션, 굿즈)
   - 감성 (힙함, 구별짓기, 레트로, 추억, 향수, SNS)
   - 큐레이션 (선별, 플레이리스트, 콘텐츠 모음, 리스트)
   - 시민 (대항 기억, 커뮤니티 기록, 구술, 사회운동)
   - 제도 (공공기록, 도서관, 법적 보존, 기관)
   - 기술 (백업, 압축, 버전관리, 소프트웨어)
   - 예술 (전시, 미술관, 영화, 음악, 창작 재료, 형식 실험)

2. implied_meaning: 이 맥락에서 '아카이브'가 실제로 뜻하는 바 (10자 이내, 한국어)

JSON으로만 응답. 다른 텍스트 없이: {{"category": "...", "implied_meaning": "..."}}"""


def classify_item(title: str, retries: int = 3) -> dict | None:
    if not GEMINI_API_KEY:
        print("[Classify] GEMINI_API_KEY not set")
        return None
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": PROMPT_TEMPLATE.format(title=title)}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024
        }
    }
    
    for attempt in range(retries):
        try:
            resp = requests.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 429:
                wait_time = (attempt + 1) * 5
                print(f"  → Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            resp.raise_for_status()
            
            result = resp.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            
            parsed = json.loads(text)
            
            if parsed.get("category") not in CATEGORIES:
                return None
            
            return parsed
        except requests.exceptions.HTTPError as e:
            if "429" in str(e):
                wait_time = (attempt + 1) * 5
                print(f"  → Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            print(f"[Classify] Error: {e}")
            return None
        except Exception as e:
            print(f"[Classify] Error: {e}")
            return None
    
    return None


def load_data() -> dict:
    with open(GHOSTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict) -> None:
    with open(GHOSTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main(limit: int = 50, dry_run: bool = False, batch_save: int = 10):
    print(f"[Classify] Starting (limit={limit}, dry_run={dry_run}, batch_save={batch_save})")
    
    data = load_data()
    items = data.get("items", [])
    
    unclassified = [item for item in items if not item.get("category")]
    print(f"[Classify] {len(unclassified)} unclassified items found")
    
    classified_count = 0
    failed_count = 0
    for i, item in enumerate(unclassified[:limit]):
        title = item.get("source_title", "")
        if not title:
            continue
        
        print(f"[Classify] [{i+1}/{min(limit, len(unclassified))}] {title[:50]}...")
        result = classify_item(title)
        
        if result:
            if not dry_run:
                item["category"] = result["category"]
                item["implied_meaning"] = result.get("implied_meaning")
            print(f"  → {result['category']} / {result.get('implied_meaning', '')}")
            classified_count += 1
        else:
            print(f"  → Failed")
            failed_count += 1
        
        # 중간 저장
        if not dry_run and classified_count > 0 and classified_count % batch_save == 0:
            data["meta"]["reviewed_count"] = sum(1 for item in items if item.get("category"))
            data["meta"]["total_count"] = len(items)
            save_data(data)
            print(f"[Classify] 중간 저장 ({classified_count}건 완료)")
        
        time.sleep(1)
    
    if not dry_run and classified_count > 0:
        data["meta"]["reviewed_count"] = sum(1 for item in items if item.get("category"))
        data["meta"]["total_count"] = len(items)
        save_data(data)
        print(f"[Classify] 최종 저장: {classified_count}건 분류, {failed_count}건 실패")
    else:
        print(f"[Classify] Would classify {classified_count} items (dry run)")
    
    print("[Classify] Done")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Classify ghost-archive items using Gemini")
    parser.add_argument("--limit", type=int, default=50, help="Max items to classify")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    
    args = parser.parse_args()
    main(limit=args.limit, dry_run=args.dry_run)
