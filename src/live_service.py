import os
import requests
import streamlit as st
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

RAPID_API_KEY = os.getenv("RAPID_API_KEY", "")
HOST = "free-cricbuzz-cricket-api.p.rapidapi.com"

@dataclass
class Fixture:
    id: int
    match_desc: str
    series_name: str
    team_a: str
    team_b: str
    venue: str
    date: str

@st.cache_data(ttl=60)
def get_fixtures(valid_teams: tuple[str, ...]) -> list[Fixture]:
    if not RAPID_API_KEY:
        st.error("Missing RAPID_API_KEY in .env file")
        return []
        
    url = f"https://{HOST}/cricket-schedule"
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": HOST,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
    except Exception as e:
        st.error(f"Failed to fetch fixtures: {e}")
        return []

    fixtures = []
    
    schedules = []
    if isinstance(data.get("response"), list):
        # depending on endpoint format
        schedules = data.get("response")
    elif isinstance(data.get("response"), dict):
        schedules = data.get("response", {}).get("schedules", [])
            
    for item in schedules:
        wrapper = item.get("scheduleAdWrapper", {})
        if not wrapper:
            continue
            
        date_str = wrapper.get("date", "Unknown Date")
        match_list = wrapper.get("matchScheduleList", [])
        
        for series in match_list:
            series_name = series.get("seriesName", "")
            for match in series.get("matchInfo", []):
                t1_raw = match.get("team1", {}).get("teamName", "")
                t2_raw = match.get("team2", {}).get("teamName", "")
                
                # Check for valid mapping or IPL. 
                # Soft match against valid_teams to help with dataset matching
                t1 = next((t for t in valid_teams if t.lower() in t1_raw.lower() or t1_raw.lower() in t.lower()), t1_raw)
                t2 = next((t for t in valid_teams if t.lower() in t2_raw.lower() or t2_raw.lower() in t.lower()), t2_raw)

                is_valid = t1 in valid_teams and t2 in valid_teams
                is_ipl = "Indian Premier League" in series_name
                
                if is_valid or is_ipl:
                    f = Fixture(
                        id=match.get("matchId", 0),
                        match_desc=match.get("matchDesc", "Match"),
                        series_name=series_name,
                        team_a=t1,
                        team_b=t2,
                        venue=match.get("venueInfo", {}).get("ground", "") + ", " + match.get("venueInfo", {}).get("city", ""),
                        date=date_str
                    )
                    fixtures.append(f)
                    
    return fixtures

@dataclass
class NewsItem:
    id: int
    headline: str
    intro: str
    context: str

@dataclass
class NewsDetail:
    id: int
    headline: str
    content: list[str]

NEWS_HOST = "crickbuzz-official-apis.p.rapidapi.com"

@st.cache_data(ttl=300)
def get_news_feed() -> list[NewsItem]:
    if not RAPID_API_KEY:
        return []
        
    url = f"https://{NEWS_HOST}/news"
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": NEWS_HOST,
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
    except Exception:
        return []

    news_list = []
    for item in data.get("storyList", []):
        story = item.get("story", {})
        if story and story.get("id"):
            news_list.append(NewsItem(
                id=story.get("id"),
                headline=story.get("hline", ""),
                intro=story.get("intro", ""),
                context=story.get("context", "")
            ))
            
    return news_list

@st.cache_data(ttl=600)
def get_news_article(news_id: int) -> NewsDetail | None:
    if not RAPID_API_KEY:
        return None
        
    url = f"https://{NEWS_HOST}/news/details/{news_id}"
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": NEWS_HOST,
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
    except Exception:
        return None

    if "headline" not in data:
        return None
        
    paragraphs = []
    for section in data.get("content", []):
        content_block = section.get("content", {})
        if content_block.get("contentType") == "text":
            val = content_block.get("contentValue", "")
            if val:
                paragraphs.append(val)
                
    return NewsDetail(
        id=news_id,
        headline=data.get("headline", ""),
        content=paragraphs
    )
