"""
SignalForge — YouTube Trend Intelligence
Backend / data layer.

Data sources:
1. My API Key       -> YOUTUBE_API_KEY from .env
2. Use my own API key -> key supplied by the user

No demo mode.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    build = None

    class HttpError(Exception):
        pass


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

if load_dotenv:
    load_dotenv(ENV_FILE)

PLATFORM_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()

# Streamlit Community Cloud fallback:
# if .env is not present, read the platform key from Secrets.
if not PLATFORM_API_KEY:
    try:
        import streamlit as st
        PLATFORM_API_KEY = str(
            st.secrets.get("YOUTUBE_API_KEY", "")
        ).strip()
    except Exception:
        PLATFORM_API_KEY = ""

REGIONS = {
    "🇮🇳 India": "IN",
    "🇺🇸 USA": "US",
    "🇩🇪 Germany": "DE",
    "🇬🇧 UK": "GB",
    "🇨🇦 Canada": "CA",
    "🌎 Worldwide": "WORLD",
}

TREND_WINDOWS = {
    "1 Hour": 1,
    "4 Hours": 4,
    "24 Hours": 24,
    "7 Days": 168,
    "1 Month": 720,
}

NICHES = [
    "personal finance",
    "investing",
    "business",
    "side hustle",
    "make money online",
    "AI tools",
    "artificial intelligence",
    "technology",
    "productivity",
    "gaming",
    "fitness",
    "health",
]

ENGLISH = {
    "en", "en-us", "en-gb", "en-ca", "en-au", "en-in"
}

HINDI = {
    "hi", "hi-in"
}

GERMAN = {
    "de", "de-de", "de-at", "de-ch"
}

REGION_LANGUAGES = {
    "IN": ENGLISH | HINDI,
    "US": ENGLISH,
    "DE": ENGLISH | GERMAN,
    "GB": ENGLISH,
    "CA": ENGLISH,
    "WORLD": ENGLISH | HINDI | GERMAN,
}


NICHE_KEYWORDS = {
    "AI & Automation": ["ai", "artificial intelligence", "chatgpt", "claude", "gemini", "agent", "automation", "llm"],
    "Finance & Investing": ["stock", "stocks", "investing", "investment", "finance", "money", "trading", "crypto", "bitcoin", "ethereum", "market", "bank", "economy"],
    "Business & Entrepreneurship": ["business", "startup", "entrepreneur", "entrepreneurship", "company", "sales", "marketing", "ecommerce", "shopify"],
    "Make Money Online": ["make money", "side hustle", "passive income", "online income", "freelance", "freelancing", "upwork", "etsy", "affiliate"],
    "Technology": ["technology", "tech", "iphone", "android", "software", "coding", "python", "programming", "developer", "computer", "gadget"],
    "Gaming": ["gaming", "gameplay", "minecraft", "fortnite", "gta", "valorant", "roblox", "playstation", "xbox", "nintendo"],
    "Health & Fitness": ["fitness", "workout", "gym", "weight loss", "diet", "nutrition", "health", "muscle", "running"],
    "Education": ["tutorial", "course", "lesson", "education", "study", "exam", "math", "science", "learn", "how to"],
    "News & Current Events": ["news", "breaking", "update", "election", "politics", "president", "war", "latest"],
    "Entertainment": ["movie", "film", "celebrity", "music", "song", "reaction", "comedy", "entertainment", "interview"],
    "Sports": ["football", "soccer", "nba", "nfl", "cricket", "tennis", "baseball", "basketball", "sports", "match"],
    "Lifestyle": ["vlog", "lifestyle", "travel", "food", "recipe", "fashion", "beauty", "home", "daily routine"],
}


def classify_niche(video: dict) -> str:
    """Simple deterministic niche classification from visible metadata."""
    snippet = video.get("snippet", {}) if isinstance(video, dict) else {}
    text = " ".join([
        str(snippet.get("title", "")),
        str(snippet.get("description", "")),
        str(snippet.get("tags", "")),
    ]).lower()

    scores = {}
    for niche, keywords in NICHE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 2 if " " in keyword else 1
        if score:
            scores[niche] = score

    if not scores:
        return "Other"
    return max(scores.items(), key=lambda x: x[1])[0]


# ============================================================
# GENERAL HELPERS
# ============================================================

def format_number(value) -> str:
    try:
        value = float(value)

        if value >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f}B"
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.1f}K"

        return f"{int(value)}"
    except Exception:
        return "0"


def safe_filename(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(text))
    return text[:100].strip("_") or "signalforge_results"


def parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except Exception:
        return datetime.now(timezone.utc)


def video_age_hours(published_at: str) -> float:
    published = parse_datetime(published_at)
    now = datetime.now(timezone.utc)

    return max(
        (now - published).total_seconds() / 3600,
        0.1,
    )


def get_language(video: dict) -> str:
    snippet = video.get("snippet", {})

    language = (
        snippet.get("defaultAudioLanguage")
        or snippet.get("defaultLanguage")
        or ""
    )

    return str(language).lower().strip()


def get_channel_country(channel: dict) -> str:
    snippet = channel.get("snippet", {})
    return str(snippet.get("country") or "").upper().strip()


def get_my_api_key() -> str:
    return PLATFORM_API_KEY


def get_selected_api_key(source: str, own_api_key: str = "") -> Optional[str]:
    if source == "Use my own API key":
        key = (own_api_key or "").strip()
        return key or None

    return PLATFORM_API_KEY or None


def validate_api_key(api_key: Optional[str]):
    if not api_key:
        return False, "No API key is configured."

    if len(api_key.strip()) < 20:
        return False, "The API key appears to be invalid."

    if build is None:
        return False, (
            "google-api-python-client is not installed. "
            "Run: pip install google-api-python-client"
        )

    return True, "API key ready."


# ============================================================
# API CLIENT
# ============================================================

def create_youtube_client(api_key: Optional[str]):
    if not api_key:
        return None

    if build is None:
        raise RuntimeError(
            "google-api-python-client is not installed."
        )

    return build(
        "youtube",
        "v3",
        developerKey=api_key,
        cache_discovery=False,
    )


def api_error_message(error: Exception) -> str:
    text = str(error)

    if "quotaExceeded" in text or "Quota exceeded" in text:
        return (
            "🚨 YouTube API quota exceeded. "
            "Switch to **Use my own API key** or wait for the quota reset."
        )

    if "rateLimitExceeded" in text:
        return (
            "⚠️ API rate limit reached. "
            "Wait a little and try again."
        )

    if "keyInvalid" in text or "API key not valid" in text:
        return "❌ API key is invalid."

    if "forbidden" in text.lower():
        return (
            "❌ YouTube API access was forbidden. "
            "Check that YouTube Data API v3 is enabled and the key restrictions are correct."
        )

    return f"YouTube API error: {text}"


# ============================================================
# CHANNEL DATA
# ============================================================

def get_channel_info(
    channel_ids,
    api_key: Optional[str],
):
    if not channel_ids or not api_key:
        return {}

    client = create_youtube_client(api_key)
    result = {}

    unique_ids = list(dict.fromkeys(
        [x for x in channel_ids if x]
    ))

    try:
        for i in range(0, len(unique_ids), 50):
            batch = unique_ids[i:i + 50]

            response = client.channels().list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch),
                maxResults=50,
            ).execute()

            for item in response.get("items", []):
                result[item["id"]] = item

    except HttpError:
        raise

    return result


def search_channel(
    query: str,
    region_code: str,
    api_key: Optional[str],
):
    client = create_youtube_client(api_key)

    kwargs = {
        "part": "snippet",
        "q": query,
        "type": "channel",
        "maxResults": 10,
    }

    if region_code != "WORLD":
        kwargs["regionCode"] = region_code

    try:
        response = client.search().list(**kwargs).execute()
        return response.get("items", [])
    except HttpError:
        raise


# ============================================================
# VIDEO FORMAT HELPERS
# ============================================================

def parse_iso8601_duration_seconds(value: str) -> int:
    """Convert a YouTube ISO-8601 duration (PT1H2M3S) to seconds."""
    if not value:
        return 0
    match = re.fullmatch(r"P(?:([0-9]+)D)?T(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+)S)?", value)
    if not match:
        return 0
    days, hours, minutes, seconds = [int(x or 0) for x in match.groups()]
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def is_long_form_video(video: dict, min_seconds: int = 240) -> bool:
    """Treat videos >= 4 minutes as long-form for creator research.

    YouTube's `videoDuration=long` means >20 minutes, which is too restrictive
    for this product. We therefore use contentDetails.duration and classify
    videos of 4+ minutes as long-form; Shorts are normally <=3 minutes.
    """
    duration = video.get("contentDetails", {}).get("duration", "")
    return parse_iso8601_duration_seconds(duration) >= min_seconds


def add_video_format_fields(df: pd.DataFrame, videos: list) -> pd.DataFrame:
    """Attach duration/format metadata to a dataframe using video IDs."""
    if df is None or df.empty:
        return df

    duration_map = {}
    for video in videos or []:
        video_id = video.get("id", "")
        duration_raw = video.get("contentDetails", {}).get("duration", "")
        seconds = parse_iso8601_duration_seconds(duration_raw)
        if video_id:
            duration_map[video_id] = seconds

    result = df.copy()

    # Support both backend/export naming and frontend naming.
    # build_video_dataframe creates "Video ID" first and adds the lowercase
    # "video_id" alias later, so duration enrichment must work with either.
    id_col = None
    for candidate in ("video_id", "Video ID", "id"):
        if candidate in result.columns:
            id_col = candidate
            break

    if id_col is None:
        # Keep the pipeline alive instead of raising KeyError.
        result["duration_seconds"] = 0
    else:
        result["duration_seconds"] = (
            result[id_col].map(duration_map).fillna(0).astype(int)
        )

    result["duration_minutes"] = (result["duration_seconds"] / 60).round(1)
    result["content_type"] = result["duration_seconds"].apply(
        lambda x: "Long-form" if x >= 240 else "Short / short-form"
    )
    result["is_long_form"] = result["duration_seconds"] >= 240
    return result


def prioritize_long_form(df: pd.DataFrame) -> pd.DataFrame:
    """Put long-form videos first while keeping Shorts available below them."""
    if df is None or df.empty or "is_long_form" not in df.columns:
        return df
    result = df.copy()
    result["_long_priority"] = result["is_long_form"].astype(int)
    sort_cols = [c for c in ["_long_priority", "trend_score", "views_per_hour", "views"] if c in result.columns]
    result = result.sort_values(sort_cols, ascending=[False] * len(sort_cols)).drop(columns=["_long_priority"], errors="ignore")
    return result.reset_index(drop=True)


# ============================================================
# VIDEO DATA
# ============================================================

def get_video_details(
    video_ids,
    api_key: Optional[str],
):
    if not video_ids or not api_key:
        return []

    client = create_youtube_client(api_key)
    videos = []

    unique_ids = list(dict.fromkeys(
        [x for x in video_ids if x]
    ))

    try:
        for i in range(0, len(unique_ids), 50):
            batch = unique_ids[i:i + 50]

            response = client.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch),
                maxResults=50,
            ).execute()

            videos.extend(response.get("items", []))

    except HttpError:
        raise

    return videos


def search_recent(
    keyword: str,
    hours: int,
    region_code: str,
    api_key: Optional[str],
    max_results: int = 25,
):
    client = create_youtube_client(api_key)

    if not client:
        raise ValueError("No API key configured.")

    published_after = (
        datetime.now(timezone.utc)
        - timedelta(hours=hours)
    ).isoformat()

    kwargs = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "order": "date",
        "publishedAfter": published_after,
        "maxResults": min(max(int(max_results), 1), 50),
    }

    if region_code != "WORLD":
        kwargs["regionCode"] = region_code

    try:
        response = client.search().list(**kwargs).execute()

        ids = [
            item["id"]["videoId"]
            for item in response.get("items", [])
            if item.get("id", {}).get("videoId")
        ]

        return get_video_details(ids, api_key)

    except HttpError:
        raise


def get_popular(
    region_code: str,
    api_key: Optional[str],
    max_results: int = 50,
):
    client = create_youtube_client(api_key)

    if not client:
        raise ValueError("No API key configured.")

    kwargs = {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "maxResults": min(max(int(max_results), 1), 50),
    }

    if region_code != "WORLD":
        kwargs["regionCode"] = region_code

    try:
        response = client.videos().list(**kwargs).execute()
        return response.get("items", [])
    except HttpError:
        raise


def get_channel_videos(
    uploads_playlist_id: str,
    api_key: Optional[str],
    max_results: int = 50,
):
    if not uploads_playlist_id:
        return []

    client = create_youtube_client(api_key)

    if not client:
        raise ValueError("No API key configured.")

    try:
        response = client.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=min(max(int(max_results), 1), 50),
        ).execute()

        ids = []

        for item in response.get("items", []):
            video_id = (
                item.get("snippet", {})
                .get("resourceId", {})
                .get("videoId")
            )

            if video_id:
                ids.append(video_id)

        return get_video_details(ids, api_key)

    except HttpError:
        raise


# ============================================================
# REGION / LANGUAGE ROUTING
# ============================================================

def region_match(
    video: dict,
    channel: dict,
    region_code: str,
) -> bool:
    if region_code == "WORLD":
        return True

    language = get_language(video)
    country = get_channel_country(channel)

    if region_code == "IN":
        return (
            country == "IN"
            or language in REGION_LANGUAGES["IN"]
        )

    if region_code in {"US", "GB", "CA"}:
        # Local channel is always eligible.
        if country == region_code:
            return True

        # English content from another country is eligible.
        if language in ENGLISH:
            return True

        return False

    if region_code == "DE":
        if country == "DE":
            return True

        if language in GERMAN:
            return True

        if language in ENGLISH:
            return True

        return False

    return True


# ============================================================
# VIDEO DATAFRAME / SCORING
# ============================================================

def build_video_dataframe(
    videos,
    region_code: str,
    api_key: Optional[str],
):
    if not videos:
        return pd.DataFrame()

    channel_ids = list({
        video.get("snippet", {}).get("channelId")
        for video in videos
        if video.get("snippet", {}).get("channelId")
    })

    channels = get_channel_info(channel_ids, api_key)
    rows = []

    for video in videos:
        snippet = video.get("snippet", {})
        stats = video.get("statistics", {})

        channel_id = snippet.get("channelId", "")
        channel = channels.get(channel_id, {})

        if not region_match(video, channel, region_code):
            continue

        try:
            views = int(stats.get("viewCount", 0))
        except (TypeError, ValueError):
            views = 0

        try:
            likes = int(stats.get("likeCount", 0))
        except (TypeError, ValueError):
            likes = 0

        try:
            comments = int(stats.get("commentCount", 0))
        except (TypeError, ValueError):
            comments = 0

        age_hours = video_age_hours(
            snippet.get("publishedAt", "")
        )

        views_per_hour = views / age_hours

        engagement = (
            ((likes + comments) / views) * 100
            if views > 0
            else 0
        )

        channel_stats = channel.get("statistics", {})

        try:
            subscribers = int(
                channel_stats.get("subscriberCount", 0)
            )
        except (TypeError, ValueError):
            subscribers = 0

        views_per_subscriber = (
            views / subscribers
            if subscribers > 0
            else 0
        )

        # Research score. This is not a prediction of future views.
        velocity_score = min(
            views_per_hour / 1000,
            100,
        )

        engagement_score = min(
            engagement * 10,
            100,
        )

        subscriber_score = min(
            views_per_subscriber * 100,
            100,
        )

        trend_score = (
            velocity_score * 0.50
            + engagement_score * 0.20
            + subscriber_score * 0.30
        )

        if trend_score >= 70:
            opportunity = "🔥 VERY HIGH"
        elif trend_score >= 50:
            opportunity = "🟢 HIGH"
        elif trend_score >= 30:
            opportunity = "🟡 MEDIUM"
        else:
            opportunity = "⚪ LOW"

        video_id = video.get("id", "")

        rows.append({
            "Title": snippet.get("title", ""),
            "Niche": classify_niche(video),
            "Channel": snippet.get("channelTitle", ""),
            "Channel Country": get_channel_country(channel),
            "Language": get_language(video),
            "Published": snippet.get("publishedAt", ""),
            "Age Hours": round(age_hours, 2),
            "Views": views,
            "Likes": likes,
            "Comments": comments,
            "Subscribers": subscribers,
            "Views/Hour": round(views_per_hour, 2),
            "Views/Subscribers": round(views_per_subscriber, 3),
            "Engagement %": round(engagement, 2),
            "Trend Score": round(trend_score, 2),
            "Opportunity": opportunity,
            "Video ID": video_id,
            "URL": f"https://www.youtube.com/watch?v={video_id}",
        })

    if not rows:
        return pd.DataFrame()

    result = (
        pd.DataFrame(rows)
        .sort_values(
            ["Trend Score", "Views/Hour"],
            ascending=False,
        )
        .reset_index(drop=True)
    )

    # Duration is available from contentDetails and lets the frontend
    # prefer long-form videos without losing Shorts completely.
    result = add_video_format_fields(result, videos)

    # --------------------------------------------------------
    # Frontend compatibility aliases
    # --------------------------------------------------------
    # The Streamlit frontend uses lowercase field names while the
    # backend's exported dataset uses readable title-case names.
    # Keep BOTH so app.py can consume the data without KeyError and
    # Excel/CSV output remains human-friendly.
    aliases = {
        "Title": "title",
        "Niche": "niche",
        "Channel": "channel",
        "Channel Country": "channel_country",
        "Language": "language",
        "Published": "published",
        "Age Hours": "age_hours",
        "Views": "views",
        "Likes": "likes",
        "Comments": "comments",
        "Subscribers": "subscribers",
        "Views/Hour": "views_per_hour",
        "Views/Subscribers": "views_per_subscribers",
        "Engagement %": "engagement",
        "Trend Score": "trend_score",
        "Opportunity": "opportunity_label",
        "Video ID": "video_id",
        "URL": "link",
        "Content Type": "content_type",
        "Duration (min)": "duration_minutes",
    }

    for source_col, alias_col in aliases.items():
        if source_col in result.columns and alias_col not in result.columns:
            result[alias_col] = result[source_col]

    # --------------------------------------------------------
    # Numeric opportunity fields for frontend calculations
    # --------------------------------------------------------
    # app.py performs mean()/sorting on lowercase `opportunity`.
    # Therefore it MUST be numeric, not the text label such as
    # "🔥 VERY HIGH".
    result["opportunity"] = pd.to_numeric(
        result["trend_score"],
        errors="coerce",
    ).fillna(0.0)

    result["opportunity_score"] = result["opportunity"].round(2)

    if "opportunity_label" not in result.columns:
        result["opportunity_label"] = ""

    return result


# ============================================================
# HIGH-LEVEL TOOLS
# ============================================================

def search_trending_candidates(
    hours: int,
    region_code: str,
    api_key: Optional[str],
    max_results: int = 50,
):
    """Fetch recent candidates without requiring a topic query.

    Uses one search call ordered by viewCount, then enriches those videos.
    For a regional search, YouTube's regionCode is a localization signal;
    it is not a historical "views by country" metric.
    """
    client = create_youtube_client(api_key)
    if not client:
        raise ValueError("No API key configured.")

    published_after = (
        datetime.now(timezone.utc) - timedelta(hours=hours)
    ).isoformat()

    kwargs = {
        "part": "snippet",
        "type": "video",
        "order": "viewCount",
        "publishedAfter": published_after,
        "maxResults": min(max(int(max_results), 1), 50),
    }
    if region_code != "WORLD":
        kwargs["regionCode"] = region_code

    response = client.search().list(**kwargs).execute()
    ids = [
        item["id"]["videoId"]
        for item in response.get("items", [])
        if item.get("id", {}).get("videoId")
    ]
    videos = get_video_details(ids, api_key)
    return videos


def discover_trending(
    api_key: Optional[str],
    region_name: str,
    window_name: str,
    results_limit: int = 30,
):
    """Region + time-window YouTube trend discovery.

    No keyword is required. Candidates are ranked by a transparent research
    score based on view velocity, total views, engagement, recency and
    views relative to channel subscribers.
    """
    region_code = REGIONS.get(region_name, region_name)
    hours = TREND_WINDOWS.get(window_name, 24)

    try:
        candidates = search_trending_candidates(
            hours,
            region_code,
            api_key,
            max_results=min(max(results_limit * 2, 30), 50),
        )

        # Add current regional popularity as a second candidate pool. This
        # costs only one videos.list request and helps surface established
        # popular videos when the recent search pool is narrow.
        try:
            popular = get_popular(
                region_code,
                api_key,
                max_results=min(50, max(results_limit, 30)),
            )
        except Exception:
            popular = []

        seen = set()
        merged = []
        for video in candidates + popular:
            vid = video.get("id")
            if not vid or vid in seen:
                continue
            seen.add(vid)
            merged.append(video)

        # For the selected window, prioritize videos actually published in
        # that window. Popularity results are retained only as context.
        now = datetime.now(timezone.utc)
        windowed = []
        for video in merged:
            published = parse_datetime(
                video.get("snippet", {}).get("publishedAt", "")
            )
            age = (now - published).total_seconds() / 3600
            if age <= hours:
                windowed.append(video)

        if not windowed:
            windowed = candidates

        df = build_video_dataframe(windowed, region_code, api_key)
        if df.empty:
            return df, None

        # Long-form is preferred for creator research, but Shorts remain in
        # the result set when they are among the strongest signals.
        df = prioritize_long_form(df)

        # Window-aware scoring. Avoid treating old high-view videos as
        # stronger trends simply because their lifetime view count is large.
        max_vph = max(float(df["views_per_hour"].max()), 1.0)
        max_views = max(float(df["views"].max()), 1.0)
        max_eng = max(float(df["engagement"].max()), 0.01)
        max_vps = max(float(df["views_per_subscribers"].max()), 0.01)

        age = df["age_hours"].clip(lower=0.1)
        recency = (1 - age / max(hours, 1)).clip(lower=0, upper=1) * 100
        velocity = (df["views_per_hour"] / max_vph * 100).clip(0, 100)
        volume = (df["views"] / max_views * 100).clip(0, 100)
        engagement = (df["engagement"] / max_eng * 100).clip(0, 100)
        breakout = (df["views_per_subscribers"] / max_vps * 100).clip(0, 100)

        df["trend_score"] = (
            velocity * 0.45
            + volume * 0.15
            + engagement * 0.15
            + breakout * 0.15
            + recency * 0.10
        ).round(2)
        df["opportunity"] = df["trend_score"]
        df["opportunity_score"] = df["trend_score"]

        df["opportunity_label"] = df["trend_score"].apply(
            lambda x: (
                "🔥 VERY HIGH" if x >= 80 else
                "🟢 HIGH" if x >= 60 else
                "🟡 MEDIUM" if x >= 40 else
                "⚪ LOW"
            )
        )
        df["Trend Score"] = df["trend_score"]
        df["Opportunity"] = df["opportunity_label"]

        return (
            df.sort_values(
                ["trend_score", "views_per_hour", "views"],
                ascending=False,
            ).head(results_limit).reset_index(drop=True),
            None,
        )

    except HttpError as e:
        return pd.DataFrame(), api_error_message(e)
    except Exception as e:
        return pd.DataFrame(), str(e)


def trend_finder(
    query: str,
    api_key: Optional[str],
    region_name: str,
    window_name: str,
    results_limit: int = 30,
):
    """Topic-specific trend finder kept for backward compatibility."""
    if not query.strip():
        return discover_trending(
            api_key,
            region_name,
            window_name,
            results_limit,
        )

    region_code = REGIONS.get(region_name, region_name)
    hours = TREND_WINDOWS.get(window_name, 24)

    try:
        videos = search_recent(
            query.strip(),
            hours,
            region_code,
            api_key,
            50,
        )
        df = build_video_dataframe(videos, region_code, api_key)
        if df.empty:
            return df, None

        # Prefer long-form (>=4 min) while keeping Shorts available.
        df = prioritize_long_form(df)
        return df.head(results_limit), None
    except HttpError as e:
        return pd.DataFrame(), api_error_message(e)
    except Exception as e:
        return pd.DataFrame(), str(e)


def keyword_scanner(
    keyword: str,
    api_key: Optional[str],
    region_name: str,
    results_limit: int = 30,
):
    # Keyword Scanner intentionally uses a 24-hour recent window.
    return trend_finder(
        keyword,
        api_key,
        region_name,
        "24 Hours",
        results_limit,
    )


def analyze_channel(
    channel_query: str,
    api_key: Optional[str],
    results_limit: int = 30,
    window_name: str = "24 Hours",
):
    if not channel_query.strip():
        return pd.DataFrame(), "Enter a channel name."

    try:
        channels = search_channel(
            channel_query.strip(),
            "WORLD",
            api_key,
        )

        if not channels:
            return pd.DataFrame(), "No channel found."

        channel_id = (
            channels[0]
            .get("snippet", {})
            .get("channelId")
        )

        if not channel_id:
            return pd.DataFrame(), "Channel ID was not found."

        channel_data = get_channel_info(
            [channel_id],
            api_key,
        ).get(channel_id, {})

        uploads_playlist = (
            channel_data
            .get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )

        if not uploads_playlist:
            return pd.DataFrame(), "Uploads playlist was not found."

        # Pull more than the display limit so top/underperforming
        # comparisons have enough rows.
        fetch_count = max(50, results_limit)

        videos = get_channel_videos(
            uploads_playlist,
            api_key,
            fetch_count,
        )

        df = build_video_dataframe(
            videos,
            "WORLD",
            api_key,
        )

        if df.empty:
            return pd.DataFrame(), "No videos found for this channel."

        return df.head(results_limit), None

    except HttpError as e:
        return pd.DataFrame(), api_error_message(e)
    except Exception as e:
        return pd.DataFrame(), str(e)


def analyze_competitors(
    names,
    api_key: Optional[str],
    videos_per_channel: int = 10,
    window_name: str = "24 Hours",
):
    names = list(dict.fromkeys([
        str(x).strip()
        for x in names
        if str(x).strip()
    ]))[:5]

    if not names:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            "Enter at least one competitor channel.",
        )

    all_frames = []
    summary_rows = []

    try:
        for requested_name in names:
            channels = search_channel(
                requested_name,
                "WORLD",
                api_key,
            )

            if not channels:
                continue

            channel_id = (
                channels[0]
                .get("snippet", {})
                .get("channelId")
            )

            if not channel_id:
                continue

            channel_data = get_channel_info(
                [channel_id],
                api_key,
            ).get(channel_id, {})

            uploads_playlist = (
                channel_data
                .get("contentDetails", {})
                .get("relatedPlaylists", {})
                .get("uploads")
            )

            if not uploads_playlist:
                continue

            videos = get_channel_videos(
                uploads_playlist,
                api_key,
                max(50, videos_per_channel),
            )

            df = build_video_dataframe(
                videos,
                "WORLD",
                api_key,
            )

            if df.empty:
                continue

            df = df.head(videos_per_channel).copy()

            competitor_name = (
                channels[0]
                .get("snippet", {})
                .get("title", requested_name)
            )

            df["Competitor"] = competitor_name
            all_frames.append(df)

            summary_rows.append({
                "Competitor": competitor_name,
                "Videos": len(df),
                "Total Views": int(df["Views"].sum()),
                "Average Views": float(df["Views"].mean()),
                "Average Views/Hour": float(df["Views/Hour"].mean()),
                "Average Engagement": float(df["Engagement %"].mean()),
                "Average Trend Score": float(df["Trend Score"].mean()),
            })

        if not all_frames:
            return (
                pd.DataFrame(),
                pd.DataFrame(),
                "No competitor video data was found.",
            )

        videos_df = pd.concat(
            all_frames,
            ignore_index=True,
        )

        summary_df = (
            pd.DataFrame(summary_rows)
            .sort_values(
                "Average Views/Hour",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        return videos_df, summary_df, None

    except HttpError as e:
        return pd.DataFrame(), pd.DataFrame(), api_error_message(e)
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), str(e)


def extract_topic_signals(
    df: pd.DataFrame,
    limit: int = 10,
):
    if df is None or df.empty or "Title" not in df.columns:
        return pd.DataFrame(
            columns=["Topic", "Mentions"]
        )

    stop_words = {
        "the", "and", "for", "with", "from", "this", "that",
        "your", "you", "how", "what", "why", "are", "was",
        "will", "new", "best", "top", "into", "about", "2026",
        "2025", "video", "full", "guide", "official", "part",
        "a", "an", "to", "of", "in", "on", "is", "it", "my",
    }

    counts = {}

    for title in df["Title"].astype(str):
        words = re.findall(
            r"[A-Za-z][A-Za-z0-9+#.-]{2,}",
            title.lower(),
        )

        for word in words:
            if word in stop_words:
                continue
            counts[word] = counts.get(word, 0) + 1

    if not counts:
        return pd.DataFrame(
            columns=["Topic", "Mentions"]
        )

    return (
        pd.DataFrame(
            [
                {"Topic": topic, "Mentions": count}
                for topic, count in counts.items()
            ]
        )
        .sort_values(
            "Mentions",
            ascending=False,
        )
        .head(limit)
        .reset_index(drop=True)
    )


# ============================================================
# EXPORT HELPERS
# ============================================================

def export_csv(df: pd.DataFrame, path):
    if df is None:
        raise ValueError("No dataframe supplied.")

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        output,
        index=False,
        encoding="utf-8-sig",
    )

    return output


def export_results(
    df: pd.DataFrame,
    path,
    sheet_name: str = "Results",
):
    if df is None:
        raise ValueError("No dataframe supplied.")

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        df.to_excel(
            writer,
            sheet_name=sheet_name[:31],
            index=False,
        )

    return output


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

# Allows older code to call the backend with the old naming style.
PLATFORM_KEY = PLATFORM_API_KEY
