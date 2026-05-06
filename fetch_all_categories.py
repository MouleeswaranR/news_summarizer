"""Batch fetch script for GitHub Actions.
Runs LangGraph pipeline for all category/region combinations and saves to cache.
"""
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import VALID_CATEGORIES, VALID_REGIONS
from graph import build_graph
from database import init_db
from cache_manager import save_to_cache


def fetch_all():
    init_db()
    graph = build_graph()

    total = len(VALID_CATEGORIES) * len(VALID_REGIONS)
    done = 0
    failed = 0

    print(f"Starting batch fetch: {total} combinations")
    print("=" * 50)

    for category in VALID_CATEGORIES:
        for region in VALID_REGIONS:
            done += 1
            print(f"[{done}/{total}] Fetching {category} / {region}...")

            try:
                state = {
                    "messages": [],
                    "category": category,
                    "region": region,
                    "date": "",
                    "raw_articles": [],
                    "filtered_articles": [],
                    "summaries": [],
                    "audio_file": None,
                    "error": None,
                }
                result = graph.invoke(state)

                if result.get("summaries"):
                    save_to_cache(category, region, result["summaries"])
                    print(f"  -> Cached {len(result['summaries'])} summaries")
                else:
                    print(f"  -> No articles found")
                    if result.get("error"):
                        print(f"     Error: {result['error']}")

            except Exception as e:
                failed += 1
                print(f"  -> FAILED: {e}")

            time.sleep(3)

    print("=" * 50)
    print(f"Done! {done - failed}/{total} succeeded, {failed} failed")


if __name__ == "__main__":
    fetch_all()
