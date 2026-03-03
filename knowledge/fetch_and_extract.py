#!/usr/bin/env python3
"""Fetch top search result pages and extract structured knowledge.
Coordinator runs this (has internet access).
Outputs structured JSON ready for Codex workers to import into DB.
"""

import json
import sys
import time
import requests
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "search_results"
EXTRACTED_DIR = Path(__file__).parent / "extracted"
EXTRACTED_DIR.mkdir(exist_ok=True)


def fetch_page_text(url: str, timeout: int = 10) -> str:
    """Fetch a page and return text content (basic HTML stripping)."""
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (compatible; MusicResearchBot/1.0)"
        })
        resp.raise_for_status()
        text = resp.text
        # Basic HTML to text
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:5000]  # First 5000 chars
    except Exception as e:
        return f"FETCH_ERROR: {e}"


def dedupe_urls(results: list[dict]) -> list[dict]:
    """Deduplicate by URL, keep first occurrence."""
    seen = set()
    deduped = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            deduped.append(r)
    return deduped


def select_top_results(results: list[dict], max_per_category: int = 15) -> list[dict]:
    """Select top results, prioritizing diverse domains."""
    deduped = dedupe_urls(results)
    # Score by relevance signals in description
    scored = []
    for r in deduped:
        score = 0
        desc = (r.get("description", "") + " " + r.get("title", "")).lower()
        # Boost educational/analytical content
        for keyword in ["theory", "analysis", "technique", "arrangement", "chord", "progression",
                       "pattern", "instrument", "melody", "harmony", "emotion", "mood",
                       "breakdown", "structure", "例", "分析", "教程"]:
            if keyword in desc:
                score += 1
        # Penalize commercial/irrelevant
        for keyword in ["buy", "subscribe", "login", "sign up", "pricing", "free trial"]:
            if keyword in desc:
                score -= 2
        scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored[:max_per_category]]


def main():
    categories = ["mood_music", "melody_accompaniment", "section_patterns",
                  "song_analysis", "tension_energy"]

    for category in categories:
        src = RESULTS_DIR / f"{category}.json"
        if not src.exists():
            print(f"Skipping {category} (no results file)", file=sys.stderr)
            continue

        results = json.loads(src.read_text())
        top = select_top_results(results, max_per_category=12)
        print(f"\n=== {category}: fetching {len(top)} pages ===", file=sys.stderr)

        enriched = []
        for i, r in enumerate(top):
            print(f"  [{i+1}/{len(top)}] {r['url'][:80]}...", file=sys.stderr)
            page_text = fetch_page_text(r["url"])
            enriched.append({
                "title": r["title"],
                "url": r["url"],
                "description": r.get("description", ""),
                "query": r.get("query", ""),
                "page_excerpt": page_text[:3000],
            })
            time.sleep(0.2)

        out_file = EXTRACTED_DIR / f"{category}_enriched.json"
        out_file.write_text(json.dumps(enriched, ensure_ascii=False, indent=2))
        print(f"  Saved {len(enriched)} enriched results -> {out_file}", file=sys.stderr)

    print("\nDone fetching!", file=sys.stderr)


if __name__ == "__main__":
    main()
