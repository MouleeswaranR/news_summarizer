from typing import TypedDict, Annotated, Optional
from pathlib import Path
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq

from config import GROQ_API_KEY, LLM_MODEL
from models import NewsSummary
from tools import fetch_newsapi, fetch_gnews
from database import save_summaries

AUDIO_DIR = Path(__file__).parent / "audio_output"


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    category: str
    region: str
    date: str
    raw_articles: list[dict]
    filtered_articles: list[dict]
    summaries: list[dict]
    audio_file: Optional[str]
    error: Optional[str]


def get_llm():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=LLM_MODEL,
        temperature=0,
    )


def fetch_node(state: AgentState) -> dict:
    """Fetch news from both APIs using tools."""
    category = state["category"]
    region = state["region"]
    date = state.get("date", "")
    articles = []
    errors = []

    print("  [Agent] Calling NewsAPI...")
    try:
        result = fetch_newsapi.invoke({"category": category, "region": region, "date": date})
        print(f"  [Agent] NewsAPI returned {len(result)} articles")
        articles.extend(result)
    except Exception as e:
        print(f"  [Agent] NewsAPI failed: {e}")
        errors.append(f"NewsAPI: {str(e)}")

    print("  [Agent] Calling GNews...")
    try:
        result = fetch_gnews.invoke({"category": category, "region": region, "date": date})
        print(f"  [Agent] GNews returned {len(result)} articles")
        articles.extend(result)
    except Exception as e:
        print(f"  [Agent] GNews failed: {e}")
        errors.append(f"GNews: {str(e)}")

    if not articles and errors:
        return {"raw_articles": [], "error": "; ".join(errors)}

    error_msg = "; ".join(errors) if errors else None
    return {"raw_articles": articles, "error": error_msg}


def filter_node(state: AgentState) -> dict:
    """Deduplicate and select top articles."""
    raw = state["raw_articles"]
    if not raw:
        return {"filtered_articles": [], "error": state.get("error")}

    seen_titles = set()
    unique = []
    for article in raw:
        title = article.get("title", "").lower().strip()
        if title and title not in seen_titles and len(title) > 10:
            seen_titles.add(title)
            unique.append(article)

    return {"filtered_articles": unique[:10]}


def summarize_node(state: AgentState) -> dict:
    """Summarize each article with sentiment and importance score."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(NewsSummary)

    summaries = []
    for article in state["filtered_articles"]:
        prompt = (
            f"Analyze and summarize this news article.\n\n"
            f"Title: {article['title']}\n"
            f"Description: {article.get('description', 'N/A')}\n"
            f"Source: {article.get('source_name', 'Unknown')}\n\n"
            f"Provide:\n"
            f"1. A 2-3 line summary\n"
            f"2. Sentiment: positive, negative, or neutral\n"
            f"3. Importance score 1-10 (10=breaking/critical, 1=minor)\n"
            f"4. 3-5 keywords\n\n"
            f"Category: {state['category']}\n"
            f"Region: {state['region']}\n"
            f"Source URL: {article.get('url', '')}"
        )

        try:
            result = structured_llm.invoke(prompt)
            summaries.append(result.model_dump())
        except Exception:
            summaries.append({
                "title": article["title"],
                "summary": article.get("description", "No summary available."),
                "sentiment": "neutral",
                "importance_score": 5,
                "keywords": [state["category"]],
                "category": state["category"],
                "source_url": article.get("url", ""),
                "region": state["region"],
            })

    return {"summaries": summaries}


def rank_node(state: AgentState) -> dict:
    """Rank summaries by importance score (highest first)."""
    summaries = state["summaries"]
    ranked = sorted(summaries, key=lambda x: x.get("importance_score", 5), reverse=True)
    return {"summaries": ranked}


def store_node(state: AgentState) -> dict:
    """Persist summaries to SQLite."""
    if state["summaries"]:
        try:
            save_summaries(state["summaries"])
        except Exception:
            pass
    return {}


def voice_node(state: AgentState) -> dict:
    """Convert top summaries to speech using gTTS (English)."""
    if not state["summaries"]:
        return {"audio_file": None}

    try:
        from gtts import gTTS

        AUDIO_DIR.mkdir(exist_ok=True)

        text_parts = []
        for i, s in enumerate(state["summaries"][:5], 1):
            text_parts.append(
                f"News {i}: {s['title']}. {s['summary']}. "
            )

        full_text = " ".join(text_parts)
        tts = gTTS(text=full_text, lang="en", slow=False)

        audio_path = AUDIO_DIR / "news_summary.mp3"
        tts.save(str(audio_path))

        return {"audio_file": str(audio_path)}
    except Exception as e:
        print(f"  [Agent] Voice generation failed: {e}")
        return {"audio_file": None}


def should_continue(state: AgentState) -> str:
    if state["filtered_articles"]:
        return "summarize"
    return "end"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("fetch", fetch_node)
    graph.add_node("filter", filter_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("rank", rank_node)
    graph.add_node("store", store_node)
    graph.add_node("voice", voice_node)

    graph.add_edge(START, "fetch")
    graph.add_edge("fetch", "filter")
    graph.add_conditional_edges(
        "filter",
        should_continue,
        {"summarize": "summarize", "end": END},
    )
    graph.add_edge("summarize", "rank")
    graph.add_edge("rank", "store")
    graph.add_edge("store", "voice")
    graph.add_edge("voice", END)

    return graph.compile()
