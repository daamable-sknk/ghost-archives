#!/usr/bin/env python3
"""
ghost-archive 자동 수집 스크립트

수집 소스:
- Google Alerts RSS (뉴스, 학술)
- Bluesky API (#아카이브, #archive)

사용법:
    python scripts/collect.py
    python scripts/collect.py --source rss
    python scripts/collect.py --source bluesky
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

# RSS 피드 URL (Google Alerts 설정 후 업데이트 필요)
RSS_FEEDS = {
    "google_alerts_ko": os.getenv("RSS_GOOGLE_ALERTS_KO", ""),
    "google_alerts_en": os.getenv("RSS_GOOGLE_ALERTS_EN", ""),
}

BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD", "")


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


# =============================================================================
# Bluesky 수집
# =============================================================================

def get_bluesky_token() -> Optional[str]:
    if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
        print("[Bluesky] Credentials not configured, skipping")
        return None
    
    try:
        resp = requests.post(
            "https://bsky.social/xrpc/com.atproto.server.createSession",
            json={"identifier": BLUESKY_HANDLE, "password": BLUESKY_APP_PASSWORD},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json().get("accessJwt")
    except Exception as e:
        print(f"[Bluesky] Auth error: {e}")
        return None


def search_bluesky(query: str, token: str, limit: int = 100) -> list:
    url = "https://bsky.social/xrpc/app.bsky.feed.searchPosts"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query, "limit": limit}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("posts", [])
    except Exception as e:
        print(f"[Bluesky] Search error for '{query}': {e}")
        return []


def collect_bluesky() -> list:
    token = get_bluesky_token()
    if not token:
        return []
    
    collected = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    search_queries = ["아카이브", "archive"]
    
    for query in search_queries:
        print(f"[Bluesky] Searching '{query}'...")
        posts = search_bluesky(query, token)
        
        for post in posts:
            record = post.get("record", {})
            text = record.get("text", "")
            uri = post.get("uri", "")
            author = post.get("author", {})
            handle = author.get("handle", "")
            
            if not text or not uri:
                continue
            
            # Bluesky 포스트 URL 생성
            # uri 형식: at://did:plc:xxx/app.bsky.feed.post/yyy
            parts = uri.split("/")
            if len(parts) >= 5:
                did = parts[2]
                post_id = parts[-1]
                post_url = f"https://bsky.app/profile/{handle}/post/{post_id}"
            else:
                post_url = uri
            
            # 날짜 파싱
            created_at = record.get("createdAt", "")
            if created_at:
                try:
                    post_date = datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime("%Y-%m-%d")
                except:
                    post_date = today
            else:
                post_date = today
            
            keyword = detect_keyword(text)
            if not keyword:
                continue
            
            # 텍스트 요약 (최대 100자)
            title = text[:100] + "..." if len(text) > 100 else text
            title = title.replace("\n", " ")
            
            item = {
                "id": generate_id(post_url, post_date),
                "source_type": "bluesky",
                "source_url": post_url,
                "source_title": title,
                "collected_at": today,
                "published_at": post_date,
                "keyword": keyword,
                "language": detect_language(text),
                "auto_collected": True,
                "reviewed": False,
                "category": None,
                "implied_meaning": None,
                "note": None
            }
            collected.append(item)
        
        print(f"[Bluesky] '{query}': {len(posts)} posts found")
    
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
    
    # Bluesky 수집
    if source is None or source == "bluesky":
        bluesky_path = SOURCES_DIR / "bluesky.json"
        bluesky_data = load_json(bluesky_path)
        
        new_items = collect_bluesky()
        bluesky_data["items"] = merge_items(bluesky_data.get("items", []), new_items)
        bluesky_data["last_fetched"] = datetime.now(timezone.utc).isoformat()
        
        save_json(bluesky_path, bluesky_data)
    
    # 메인 데이터 업데이트
    update_main_data()
    
    print(f"[Done]")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ghost-archive collector")
    parser.add_argument("--source", choices=["rss", "bluesky"], help="Collect from specific source only")
    
    args = parser.parse_args()
    main(source=args.source)
