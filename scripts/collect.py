#!/usr/bin/env python3
"""
ghost-archive 자동 수집 스크립트

수집 소스:
- Google News RSS (한국어/영어)
- Naver News API (한국어)

사용법:
    python scripts/collect.py
    python scripts/collect.py --source rss
    python scripts/collect.py --source naver
"""

import json
import os
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import feedparser
import requests

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SOURCES_DIR = DATA_DIR / "sources"

# 검색 키워드
KEYWORDS = {
    "ko": ["아카이브", "아카이빙"],
    "en": ["archive", "archiving", "archived"]
}

RSS_FEEDS = {
    "google_news_ko": "https://news.google.com/rss/search?q=%EC%95%84%EC%B9%B4%EC%9D%B4%EB%B8%8C&hl=ko&gl=KR&ceid=KR:ko",
    "google_news_en": "https://news.google.com/rss/search?q=archive&hl=en-US&gl=US&ceid=US:en",
}

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")


def generate_id(url: str, date: str) -> str:
    """URL과 날짜 기반 고유 ID 생성"""
    hash_input = f"{url}{date}"
    short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
    return f"ghost-{date}-{short_hash}"


def detect_language(text: str) -> str:
    """간단한 언어 감지 (한글 포함 여부)"""
    if re.search(r'[가-힣]', text):
        return "ko"
    return "en"


def detect_keyword(text: str) -> Optional[str]:
    """텍스트에서 키워드 감지"""
    text_lower = text.lower()
    for lang, keywords in KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return keyword
    return None


def load_json(path: Path) -> dict:
    """JSON 파일 로드"""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"items": []}


def save_json(path: Path, data: dict) -> None:
    """JSON 파일 저장"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_existing_urls(data: dict) -> set:
    """기존 URL 목록 추출"""
    return {item.get("source_url") for item in data.get("items", [])}


# =============================================================================
# RSS 수집
# =============================================================================

def collect_rss() -> list:
    """RSS 피드에서 수집"""
    collected = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    for feed_name, feed_url in RSS_FEEDS.items():
        if not feed_url:
            print(f"[RSS] {feed_name}: URL not configured, skipping")
            continue
            
        print(f"[RSS] Fetching {feed_name}...")
        
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                url = entry.get("link", "")
                title = entry.get("title", "")
                
                if not url or not title:
                    continue
                
                # 날짜 파싱
                published = entry.get("published_parsed")
                if published:
                    entry_date = datetime(*published[:6]).strftime("%Y-%m-%d")
                else:
                    entry_date = today
                
                keyword = detect_keyword(title)
                if not keyword:
                    continue
                
                item = {
                    "id": generate_id(url, entry_date),
                    "source_type": "news",
                    "source_url": url,
                    "source_title": title,
                    "collected_at": today,
                    "published_at": entry_date,
                    "keyword": keyword,
                    "language": detect_language(title),
                    "auto_collected": True,
                    "reviewed": False,
                    "category": None,
                    "implied_meaning": None,
                    "note": None
                }
                collected.append(item)
                
            print(f"[RSS] {feed_name}: {len(feed.entries)} entries found")
            
        except Exception as e:
            print(f"[RSS] {feed_name}: Error - {e}")
    
    return collected


def collect_naver() -> list:
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("[Naver] Credentials not configured, skipping")
        return []
    
    collected = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    search_queries = ["아카이브", "아카이빙"]
    
    for query in search_queries:
        print(f"[Naver] Searching '{query}'...")
        
        try:
            params = {"query": query, "display": 100, "sort": "date"}
            resp = requests.get(
                "https://openapi.naver.com/v1/search/news.json",
                headers=headers, params=params, timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            
            for item_data in data.get("items", []):
                url = item_data.get("originallink") or item_data.get("link", "")
                title = re.sub(r'<[^>]+>', '', item_data.get("title", ""))
                
                if not url or not title:
                    continue
                
                pub_date = item_data.get("pubDate", "")
                if pub_date:
                    try:
                        from email.utils import parsedate_to_datetime
                        entry_date = parsedate_to_datetime(pub_date).strftime("%Y-%m-%d")
                    except:
                        entry_date = today
                else:
                    entry_date = today
                
                keyword = detect_keyword(title)
                if not keyword:
                    continue
                
                item = {
                    "id": generate_id(url, entry_date),
                    "source_type": "news",
                    "source_url": url,
                    "source_title": title,
                    "collected_at": today,
                    "published_at": entry_date,
                    "keyword": keyword,
                    "language": "ko",
                    "auto_collected": True,
                    "reviewed": False,
                    "category": None,
                    "implied_meaning": None,
                    "note": None
                }
                collected.append(item)
            
            print(f"[Naver] '{query}': {len(data.get('items', []))} items found")
            
        except Exception as e:
            print(f"[Naver] '{query}': Error - {e}")
    
    return collected


# =============================================================================
# 메인 로직
# =============================================================================

def merge_items(existing: list, new: list) -> list:
    """기존 항목과 새 항목 병합 (중복 제거)"""
    existing_urls = {item.get("source_url") for item in existing}
    
    merged = existing.copy()
    added = 0
    
    for item in new:
        if item.get("source_url") not in existing_urls:
            merged.append(item)
            existing_urls.add(item.get("source_url"))
            added += 1
    
    print(f"[Merge] {added} new items added, {len(merged)} total")
    return merged


def update_main_data():
    """메인 ghosts.json 업데이트"""
    main_path = DATA_DIR / "ghosts.json"
    main_data = load_json(main_path)
    
    # 각 소스에서 데이터 로드
    all_items = main_data.get("items", [])
    
    for source_file in SOURCES_DIR.glob("*.json"):
        source_data = load_json(source_file)
        source_items = source_data.get("items", [])
        all_items = merge_items(all_items, source_items)
    
    # 날짜순 정렬 (최신순)
    all_items.sort(key=lambda x: x.get("collected_at", ""), reverse=True)
    
    # 통계 업데이트
    reviewed_count = sum(1 for item in all_items if item.get("reviewed"))
    
    main_data = {
        "meta": {
            "title": "ghost-archive",
            "description": "'아카이브'라는 단어의 용례 수집",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_count": len(all_items),
            "reviewed_count": reviewed_count
        },
        "items": all_items
    }
    
    save_json(main_path, main_data)
    print(f"[Main] Updated ghosts.json: {len(all_items)} items")


def main(source: Optional[str] = None):
    """메인 실행"""
    print(f"[Start] ghost-archive collector")
    print(f"[Time] {datetime.now(timezone.utc).isoformat()}")
    
    # RSS 수집
    if source is None or source == "rss":
        rss_path = SOURCES_DIR / "rss.json"
        rss_data = load_json(rss_path)
        
        new_items = collect_rss()
        rss_data["items"] = merge_items(rss_data.get("items", []), new_items)
        rss_data["last_fetched"] = datetime.now(timezone.utc).isoformat()
        
        save_json(rss_path, rss_data)
    
    # Naver 수집
    if source is None or source == "naver":
        naver_path = SOURCES_DIR / "naver.json"
        naver_data = load_json(naver_path)
        
        new_items = collect_naver()
        naver_data["items"] = merge_items(naver_data.get("items", []), new_items)
        naver_data["last_fetched"] = datetime.now(timezone.utc).isoformat()
        
        save_json(naver_path, naver_data)
    
    # 메인 데이터 업데이트
    update_main_data()
    
    print(f"[Done]")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ghost-archive collector")
    parser.add_argument("--source", choices=["rss", "naver"], help="Collect from specific source only")
    
    args = parser.parse_args()
    main(source=args.source)
