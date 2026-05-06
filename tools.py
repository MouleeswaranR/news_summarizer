import requests
import urllib3
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from config import NEWS_API_KEY, GNEWS_API_KEY, GROQ_API_KEY, LLM_MODEL

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@tool
def fetch_newsapi(category: str, region: str, date: str = "", state: str = "") -> list[dict]:
    """Fetch headlines from NewsAPI.org based on category, region, date, and state.

    Args:
        category: News category (technology, sports, business, health, science, entertainment, general)
        region: Either 'india' or 'global'
        date: Specific date in YYYY-MM-DD format. If empty, fetches today's news.
        state: Indian state name for state-wise filtering. If empty, no state filter.
    """
    country = "in" if region == "india" else "us"

    if state or date:
        url = "https://newsapi.org/v2/everything"
        q_parts = []
        if state:
            q_parts.append(f'"{state}"')
        if category == "politics":
            q_parts.append("(politics OR government OR election OR minister)")
        elif category != "general":
            q_parts.append(category)
        else:
            q_parts.append("news")
        q = " AND ".join(q_parts)
        params = {
            "apiKey": NEWS_API_KEY,
            "q": q,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 10,
        }
        if date:
            params["from"] = date
            params["to"] = date
    elif category == "politics":
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": NEWS_API_KEY,
            "q": "politics OR government OR election OR minister OR parliament",
            "country": country,
            "pageSize": 10,
        }
    else:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": NEWS_API_KEY,
            "category": category,
            "country": country,
            "pageSize": 10,
        }

    response = requests.get(url, params=params, timeout=30, verify=False)
    response.raise_for_status()
    data = response.json()

    if data.get("status") == "error":
        raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")

    articles = []
    for item in data.get("articles", []):
        if item.get("title") and item["title"] != "[Removed]":
            articles.append({
                "title": item.get("title", ""),
                "description": item.get("description", "") or "",
                "url": item.get("url", ""),
                "source_name": item.get("source", {}).get("name", "Unknown"),
                "published_at": item.get("publishedAt", ""),
            })

    return articles


@tool
def fetch_gnews(category: str, region: str, date: str = "", state: str = "") -> list[dict]:
    """Fetch headlines from GNews.io based on category, region, date, and state.

    Args:
        category: News category (technology, sports, business, health, science, entertainment, general)
        region: Either 'india' or 'global'
        date: Specific date in YYYY-MM-DD format. If empty, fetches today's news.
        state: Indian state name for state-wise filtering. If empty, no state filter.
    """
    country = "in" if region == "india" else "us"

    GNEWS_CATEGORY_MAP = {
        "technology": "technology",
        "sports": "sports",
        "business": "business",
        "health": "health",
        "science": "science",
        "entertainment": "entertainment",
        "general": "general",
        "politics": "nation",
    }

    gnews_category = GNEWS_CATEGORY_MAP.get(category, "general")

    if state or category == "politics" or date:
        url = "https://gnews.io/api/v4/search"
        q_parts = []
        if state:
            q_parts.append(f'"{state}"')
        if category == "politics":
            q_parts.append("politics OR government OR election OR minister")
        elif category != "general":
            q_parts.append(category)
        else:
            q_parts.append("news")
        q = " ".join(q_parts)
        params = {
            "apikey": GNEWS_API_KEY,
            "q": q,
            "country": country,
            "lang": "en",
            "max": 10,
        }
        if date:
            params["from"] = f"{date}T00:00:00Z"
            params["to"] = f"{date}T23:59:59Z"
    else:
        url = "https://gnews.io/api/v4/top-headlines"
        params = {
            "apikey": GNEWS_API_KEY,
            "category": gnews_category,
            "country": country,
            "lang": "en",
            "max": 10,
        }

    response = requests.get(url, params=params, timeout=30, verify=False)
    response.raise_for_status()
    data = response.json()

    articles = []
    for item in data.get("articles", []):
        if item.get("title"):
            articles.append({
                "title": item.get("title", ""),
                "description": item.get("description", "") or "",
                "url": item.get("url", ""),
                "source_name": item.get("source", {}).get("name", "Unknown"),
                "published_at": item.get("publishedAt", ""),
            })

    return articles


@tool
def fetch_article_details(url: str, title: str) -> str:
    """Fetch full article content from a URL and extract the main text.

    Args:
        url: The URL of the news article to fetch details from.
        title: The title of the article for context.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        article_text = " ".join(p.get_text().strip() for p in paragraphs[:15])

        if len(article_text) < 50:
            article_text = soup.get_text(separator=" ", strip=True)[:2000]

        return article_text[:3000]
    except Exception as e:
        return f"Could not fetch article: {str(e)}"


def get_why_it_matters(title: str, summary: str, source_url: str) -> str:
    """Fetch article details online and generate 'Why it matters' using LLM."""
    article_content = fetch_article_details.invoke({"url": source_url, "title": title})

    llm = ChatGroq(api_key=GROQ_API_KEY, model=LLM_MODEL, temperature=0)

    prompt = (
        f"Based on this news article, explain WHY IT MATTERS to the reader in 2-3 sentences. "
        f"Focus on real-world impact, consequences, and what it means for people.\n\n"
        f"Title: {title}\n"
        f"Summary: {summary}\n"
        f"Full Article Content:\n{article_content}\n\n"
        f"Give ONLY the 'Why it matters' explanation, nothing else."
    )

    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Could not generate explanation: {str(e)}"
