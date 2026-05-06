import argparse
from graph import build_graph
from database import init_db
from config import VALID_CATEGORIES, VALID_REGIONS

SENTIMENT_ICONS = {"positive": "+", "negative": "-", "neutral": "~"}


def run():
    """Autonomous News Summarizer Agent — Fetch, Summarize, Rank, Highlight."""
    parser = argparse.ArgumentParser(description="Autonomous News Summarizer Agent")
    parser.add_argument("--category", choices=VALID_CATEGORIES, default="general", help="News category")
    parser.add_argument("--region", choices=VALID_REGIONS, default="india", help="News region")
    parser.add_argument("--date", type=str, default="", help="Specific date (YYYY-MM-DD) to fetch news from")
    parser.add_argument("--no-voice", action="store_true", help="Skip voice summary generation")
    args = parser.parse_args()

    init_db()

    graph = build_graph()
    initial_state = {
        "messages": [],
        "category": args.category,
        "region": args.region,
        "date": args.date,
        "raw_articles": [],
        "filtered_articles": [],
        "summaries": [],
        "audio_file": None,
        "error": None,
    }

    date_info = f" for date {args.date}" if args.date else ""
    print(f"\nFetching {args.category} news for {args.region}{date_info}...\n")
    result = graph.invoke(initial_state)

    if result.get("error"):
        print(f"Warning: {result['error']}\n")

    if not result["summaries"]:
        print("No news articles found.")
        return

    print(f"{'=' * 65}")
    print(f"  NEWS SUMMARIES — {args.category.upper()} ({args.region.upper()}) | Ranked by Importance")
    if args.date:
        print(f"  Date: {args.date}")
    print(f"{'=' * 65}\n")

    for i, s in enumerate(result["summaries"], 1):
        sentiment_icon = SENTIMENT_ICONS.get(s.get("sentiment", "neutral"), "~")
        score = s.get("importance_score", 5)

        print(f"  {i}. [{sentiment_icon}] [Score: {score}/10] {s['title']}")
        print(f"     {s['summary']}")
        print(f"     Keywords: {', '.join(s['keywords'])}")
        print(f"     Sentiment: {s.get('sentiment', 'neutral')} | Source: {s['source_url']}")
        print()

    if result.get("audio_file"):
        print(f"  Audio summary: {result['audio_file']}")
    print()


if __name__ == "__main__":
    run()
