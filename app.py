import streamlit as st
import json
from datetime import date, timedelta
from pathlib import Path
from graph import build_graph
from database import init_db, query_summaries
from tools import get_why_it_matters
from config import VALID_CATEGORIES, VALID_REGIONS

SENTIMENT_EMOJI = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}

st.set_page_config(page_title="News Summarizer Agent", layout="wide")
st.title("Autonomous News Summarizer Agent")
st.caption("Powered by LangGraph + Groq (Llama 3.3 70B) | NewsAPI + GNews")

with st.sidebar:
    st.header("Settings")
    category = st.selectbox("Category", VALID_CATEGORIES, index=0)
    region = st.selectbox("Region", VALID_REGIONS, index=0)

    st.subheader("Date Filter")
    use_date = st.checkbox("Fetch news for a specific date")
    selected_date = ""
    if use_date:
        date_input = st.date_input(
            "Select date",
            value=date.today(),
            min_value=date.today() - timedelta(days=30),
            max_value=date.today(),
        )
        selected_date = date_input.strftime("%Y-%m-%d")

    fetch_btn = st.button("Fetch & Summarize", type="primary", use_container_width=True)

    st.divider()
    st.header("History")
    show_history = st.button("Show Past Summaries", use_container_width=True)

if fetch_btn:
    init_db()
    graph = build_graph()

    with st.spinner("Fetching news and generating summaries..."):
        initial_state = {
            "messages": [],
            "category": category,
            "region": region,
            "date": selected_date,
            "raw_articles": [],
            "filtered_articles": [],
            "summaries": [],
            "audio_file": None,
            "error": None,
        }
        result = graph.invoke(initial_state)

    if result.get("error"):
        st.warning(result["error"])

    if result["summaries"]:
        st.session_state["summaries"] = result["summaries"]
        st.session_state["audio_file"] = result.get("audio_file")

if "summaries" in st.session_state and st.session_state["summaries"]:
    summaries = st.session_state["summaries"]

    title_text = f"Top {category.title()} News — {region.title()}"
    if selected_date:
        title_text += f" | Date: {selected_date}"
    st.subheader(title_text)

    cols = st.columns(2)
    for i, s in enumerate(summaries):
        with cols[i % 2]:
            with st.container(border=True):
                sentiment = s.get("sentiment", "neutral")
                score = s.get("importance_score", 5)
                emoji = SENTIMENT_EMOJI.get(sentiment, "🟡")

                st.markdown(f"**{emoji} {s['title']}**")
                st.caption(f"Importance: {'⭐' * min(score, 10)} ({score}/10) | Sentiment: {sentiment}")
                st.write(s["summary"])

                keywords_str = ", ".join(s["keywords"]) if isinstance(s["keywords"], list) else s["keywords"]
                st.caption(f"Keywords: {keywords_str}")
                st.caption(f"Category: {s['category']} | Region: {s['region']}")

                col1, col2 = st.columns(2)
                with col1:
                    if s.get("source_url"):
                        st.link_button("Read Full Article", s["source_url"])
                with col2:
                    btn_key = f"why_{i}"
                    if st.button("💡 Why it matters?", key=btn_key):
                        with st.spinner("Fetching article details..."):
                            explanation = get_why_it_matters(
                                title=s["title"],
                                summary=s["summary"],
                                source_url=s.get("source_url", ""),
                            )
                        st.success(f"**Why it matters:** {explanation}")

    # Audio player
    audio_file = st.session_state.get("audio_file")
    if audio_file:
        audio_path = Path(audio_file)
        if audio_path.exists():
            st.divider()
            st.subheader("🔊 Voice Summary")
            st.audio(str(audio_path), format="audio/mp3")

elif not fetch_btn:
    st.info("Select a category and region, then click 'Fetch & Summarize' to get started.")

if show_history:
    init_db()
    past = query_summaries(category=category, region=region, limit=20)
    if past:
        st.subheader("Past Summaries")
        for item in past:
            sentiment = item.get("sentiment", "neutral")
            emoji = SENTIMENT_EMOJI.get(sentiment, "🟡")
            with st.expander(f"{emoji} {item['title']} — {item['created_at']}"):
                st.write(item["summary"])
                keywords = item["keywords"]
                if isinstance(keywords, str):
                    try:
                        keywords = ", ".join(json.loads(keywords))
                    except json.JSONDecodeError:
                        pass
                st.caption(f"Keywords: {keywords} | Sentiment: {sentiment} | Score: {item.get('importance_score', 'N/A')}/10")
    else:
        st.info("No past summaries found for this filter.")
