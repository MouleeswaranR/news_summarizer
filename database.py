import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent / "news_summaries.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            sentiment TEXT DEFAULT 'neutral',
            importance_score INTEGER DEFAULT 5,
            keywords TEXT NOT NULL,
            category TEXT NOT NULL,
            source_url TEXT NOT NULL,
            region TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_summaries(summaries: list[dict]):
    conn = get_connection()
    for s in summaries:
        conn.execute(
            """INSERT INTO summaries
               (title, summary, sentiment, importance_score, keywords, category, source_url, region)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                s["title"],
                s["summary"],
                s.get("sentiment", "neutral"),
                s.get("importance_score", 5),
                json.dumps(s["keywords"]),
                s["category"],
                s["source_url"],
                s["region"],
            ),
        )
    conn.commit()
    conn.close()


def query_summaries(category: str = None, region: str = None, limit: int = 20) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM summaries WHERE 1=1"
    params: list = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if region:
        query += " AND region = ?"
        params.append(region)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]
