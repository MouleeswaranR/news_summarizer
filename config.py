import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")

LLM_MODEL = "llama-3.3-70b-versatile"

VALID_CATEGORIES = [
    "technology", "sports", "politics", "business",
    "health", "science", "entertainment", "general",
]

VALID_REGIONS = ["india", "global"]
