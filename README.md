# Autonomous News Summarizer Agent

A LangGraph-based agent that fetches, filters, summarizes, and highlights news from multiple sources using free LLM (Groq - Llama 3.3 70B).

## Features

- **LangGraph StateGraph** — structured agent pipeline with typed state
- **Tools** — `fetch_newsapi` + `fetch_gnews` as LangGraph tools (agent decides which to call)
- **Structured Output** — Pydantic models enforce clean JSON (title, summary, keywords, category)
- **Free LLM** — Groq (Llama 3.3 70B) for summarization
- **Dual Interface** — CLI + Streamlit web dashboard
- **SQLite Memory** — persists summaries across runs
- **Categories** — technology, sports, politics, business, health, science, entertainment, general
- **Regions** — India + Global news

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

Get free API keys:
- **Groq**: https://console.groq.com (free tier)
- **NewsAPI**: https://newsapi.org (free developer plan)
- **GNews**: https://gnews.io (free tier)

3. Run CLI:
```bash
python main.py --category technology --region india
```

4. Run Streamlit dashboard:
```bash
streamlit run app.py
```

## Agent Flow (LangGraph)

```
START → fetch (ReAct agent with tools) → filter (deduplicate) → summarize (structured output) → highlight → store (SQLite) → END
```

## Project Structure

```
├── main.py          # CLI entry point
├── app.py           # Streamlit web dashboard
├── graph.py         # LangGraph StateGraph definition
├── tools.py         # @tool decorated news fetchers
├── models.py        # Pydantic structured output models
├── database.py      # SQLite persistence layer
├── config.py        # Environment configuration
├── .env.example     # API key template
└── requirements.txt # Python dependencies
```
