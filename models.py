from pydantic import BaseModel, Field
from enum import Enum


class Category(str, Enum):
    TECHNOLOGY = "technology"
    SPORTS = "sports"
    POLITICS = "politics"
    BUSINESS = "business"
    HEALTH = "health"
    SCIENCE = "science"
    ENTERTAINMENT = "entertainment"
    GENERAL = "general"


class Region(str, Enum):
    INDIA = "india"
    GLOBAL = "global"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class NewsSummary(BaseModel):
    title: str = Field(description="Original headline of the article")
    summary: str = Field(description="2-3 line concise summary of the article")
    sentiment: str = Field(description="Sentiment of the news: positive, negative, or neutral")
    importance_score: int = Field(description="Importance score from 1-10 (10 = breaking/critical news, 1 = minor)")
    keywords: list[str] = Field(description="3-5 relevant keywords or topics")
    category: str = Field(description="Category: technology, sports, politics, business, health, science, entertainment, general")
    source_url: str = Field(description="URL to the original article")
    region: str = Field(description="Region: india or global")
