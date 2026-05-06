import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_FILE = CACHE_DIR / "news_cache.json"
IST = timezone(timedelta(hours=5, minutes=30))


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return {"last_updated": None, "data": {}}
    return {"last_updated": None, "data": {}}


def load_cached_summaries(category: str, region: str) -> list[dict] | None:
    cache = _load_cache()
    key = f"{category}_{region}"
    entry = cache.get("data", {}).get(key)
    if entry:
        return entry.get("summaries", [])
    return None


def get_cache_age_hours(category: str, region: str) -> float | None:
    cache = _load_cache()
    key = f"{category}_{region}"
    entry = cache.get("data", {}).get(key)
    if entry and entry.get("fetched_at"):
        fetched = datetime.fromisoformat(entry["fetched_at"])
        now = datetime.now(IST)
        return (now - fetched).total_seconds() / 3600
    return None


def is_cache_fresh(category: str, region: str, max_age_hours: float = 6.0) -> bool:
    age = get_cache_age_hours(category, region)
    if age is None:
        return False
    return age < max_age_hours


def save_to_cache(category: str, region: str, summaries: list[dict]):
    CACHE_DIR.mkdir(exist_ok=True)
    cache = _load_cache()
    key = f"{category}_{region}"
    cache["data"][key] = {
        "fetched_at": datetime.now(IST).isoformat(),
        "summaries": summaries,
    }
    cache["last_updated"] = datetime.now(IST).isoformat()
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
