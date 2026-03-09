#!/usr/bin/env python3
"""Brave Search API utility for music theory knowledge gathering.

Usage:
    python brave_search.py "chord progressions jazz" --count 20 --out results.json
    python brave_search.py --batch queries.txt --out results.json
"""

import argparse
import json
import os
import sys
import time
import requests
from pathlib import Path

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
BRAVE_URL = "https://api.search.brave.com/res/v1/web/search"

HEADERS = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
    "X-Subscription-Token": BRAVE_API_KEY,
}


def search(query: str, count: int = 20, freshness: str = "", offset: int = 0) -> list[dict]:
    """Search Brave and return results."""
    params = {"q": query, "count": min(count, 20), "offset": offset}
    if freshness:
        params["freshness"] = freshness
    try:
        resp = requests.get(BRAVE_URL, headers=HEADERS, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("web", {}).get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "description": r.get("description", ""),
                "query": query,
            }
            for r in results
        ]
    except Exception as e:
        print(f"Search error for '{query}': {e}", file=sys.stderr)
        return []


def batch_search(queries: list[str], count: int = 20, delay: float = 0.05) -> list[dict]:
    """Run multiple searches with rate limiting. 50 req/s = 0.02s gap, using 0.05s for safety."""
    all_results = []
    for i, q in enumerate(queries):
        results = search(q, count=count)
        all_results.extend(results)
        if i < len(queries) - 1:
            time.sleep(delay)
    return all_results


def main():
    parser = argparse.ArgumentParser(description="Brave Search for music theory")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--batch", help="File with one query per line")
    parser.add_argument("--count", type=int, default=20, help="Results per query")
    parser.add_argument("--out", default="results.json", help="Output file")
    parser.add_argument("--delay", type=float, default=0.05, help="Delay between queries (seconds)")
    args = parser.parse_args()

    if args.batch:
        queries = Path(args.batch).read_text().strip().splitlines()
        queries = [q.strip() for q in queries if q.strip()]
    elif args.query:
        queries = [args.query]
    else:
        parser.error("Provide a query or --batch file")

    print(f"Searching {len(queries)} queries, {args.count} results each...", file=sys.stderr)
    results = batch_search(queries, count=args.count, delay=args.delay)
    print(f"Got {len(results)} total results", file=sys.stderr)

    Path(args.out).write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Saved to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
