import os
from pathlib import Path


def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit Cloud secrets or environment variables."""
    try:
        import streamlit as st
        return st.secrets[key]
    except (KeyError, AttributeError, FileNotFoundError, ImportError):
        pass

    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    return os.getenv(key, default)


GROQ_API_KEY = get_secret("GROQ_API_KEY")
NEWS_API_KEY = get_secret("NEWS_API_KEY")
GNEWS_API_KEY = get_secret("GNEWS_API_KEY")

LLM_MODEL = "llama-3.3-70b-versatile"

VALID_CATEGORIES = [
    "technology", "sports", "politics", "business",
    "health", "science", "entertainment", "general",
]

VALID_REGIONS = ["india", "global"]

INDIAN_STATES = [
    "Tamil Nadu", "Karnataka", "Kerala", "Andhra Pradesh", "Telangana",
    "Maharashtra", "Gujarat", "Rajasthan", "Uttar Pradesh", "Madhya Pradesh",
    "West Bengal", "Bihar", "Odisha", "Punjab", "Haryana",
    "Jharkhand", "Chhattisgarh", "Assam", "Goa", "Himachal Pradesh",
    "Uttarakhand", "Delhi", "Jammu and Kashmir", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Sikkim", "Tripura", "Arunachal Pradesh",
]
