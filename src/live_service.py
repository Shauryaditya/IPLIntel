from __future__ import annotations

from dataclasses import dataclass
from datetime import date


TOURNAMENT_NAME = "Indian Premier League 2026"

TEAM_NAMES = {
    "CSK": "Chennai Super Kings",
    "DC": "Delhi Capitals",
    "GT": "Gujarat Titans",
    "KKR": "Kolkata Knight Riders",
    "LSG": "Lucknow Super Giants",
    "MI": "Mumbai Indians",
    "PBKS": "Punjab Kings",
    "RCB": "Royal Challengers Bengaluru",
    "RR": "Rajasthan Royals",
    "SRH": "Sunrisers Hyderabad",
}

VENUE_NAMES = {
    "Ahmedabad": "Narendra Modi Stadium, Ahmedabad",
    "Bengaluru": "M Chinnaswamy Stadium, Bengaluru",
    "Chennai": "MA Chidambaram Stadium, Chepauk, Chennai",
    "Delhi": "Arun Jaitley Stadium, Delhi",
    "Dharamsala": "Himachal Pradesh Cricket Association Stadium, Dharamsala",
    "Guwahati": "Barsapara Cricket Stadium, Guwahati",
    "Hyderabad": "Rajiv Gandhi International Stadium, Uppal, Hyderabad",
    "Jaipur": "Sawai Mansingh Stadium, Jaipur",
    "Kolkata": "Eden Gardens, Kolkata",
    "Lucknow": "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow",
    "Mumbai": "Wankhede Stadium, Mumbai",
    "New Chandigarh": "Maharaja Yadavindra Singh International Cricket Stadium, New Chandigarh",
    "Raipur": "Shaheed Veer Narayan Singh International Stadium",
}

RAW_FIXTURES = (
    (1, "2026-03-28", "19:30", "RCB", "SRH", "Bengaluru"),
    (2, "2026-03-29", "19:30", "MI", "KKR", "Mumbai"),
    (3, "2026-03-30", "19:30", "RR", "CSK", "Guwahati"),
    (4, "2026-03-31", "19:30", "PBKS", "GT", "New Chandigarh"),
    (5, "2026-04-01", "19:30", "LSG", "DC", "Lucknow"),
    (6, "2026-04-02", "19:30", "KKR", "SRH", "Kolkata"),
    (7, "2026-04-03", "19:30", "CSK", "PBKS", "Chennai"),
    (8, "2026-04-04", "15:30", "DC", "MI", "Delhi"),
    (9, "2026-04-04", "19:30", "GT", "RR", "Ahmedabad"),
    (10, "2026-04-05", "15:30", "SRH", "LSG", "Hyderabad"),
    (11, "2026-04-05", "19:30", "RCB", "CSK", "Bengaluru"),
    (12, "2026-04-06", "19:30", "KKR", "PBKS", "Kolkata"),
    (13, "2026-04-07", "19:30", "RR", "MI", "Guwahati"),
    (14, "2026-04-08", "19:30", "DC", "GT", "Delhi"),
    (15, "2026-04-09", "19:30", "KKR", "LSG", "Kolkata"),
    (16, "2026-04-10", "19:30", "RR", "RCB", "Guwahati"),
    (17, "2026-04-11", "15:30", "PBKS", "SRH", "New Chandigarh"),
    (18, "2026-04-11", "19:30", "CSK", "DC", "Chennai"),
    (19, "2026-04-12", "15:30", "LSG", "GT", "Lucknow"),
    (20, "2026-04-12", "19:30", "MI", "RCB", "Mumbai"),
    (21, "2026-04-13", "19:30", "SRH", "RR", "Hyderabad"),
    (22, "2026-04-14", "19:30", "CSK", "KKR", "Chennai"),
    (23, "2026-04-15", "19:30", "RCB", "LSG", "Bengaluru"),
    (24, "2026-04-16", "19:30", "MI", "PBKS", "Mumbai"),
    (25, "2026-04-17", "19:30", "GT", "KKR", "Ahmedabad"),
    (26, "2026-04-18", "15:30", "RCB", "DC", "Bengaluru"),
    (27, "2026-04-18", "19:30", "SRH", "CSK", "Hyderabad"),
    (28, "2026-04-19", "15:30", "KKR", "RR", "Kolkata"),
    (29, "2026-04-19", "19:30", "PBKS", "LSG", "New Chandigarh"),
    (30, "2026-04-20", "19:30", "GT", "MI", "Ahmedabad"),
    (31, "2026-04-21", "19:30", "SRH", "DC", "Hyderabad"),
    (32, "2026-04-22", "19:30", "LSG", "RR", "Lucknow"),
    (33, "2026-04-23", "19:30", "MI", "CSK", "Mumbai"),
    (34, "2026-04-24", "19:30", "RCB", "GT", "Bengaluru"),
    (35, "2026-04-25", "15:30", "DC", "PBKS", "Delhi"),
    (36, "2026-04-25", "19:30", "RR", "SRH", "Jaipur"),
    (37, "2026-04-26", "15:30", "GT", "CSK", "Ahmedabad"),
    (38, "2026-04-26", "19:30", "LSG", "KKR", "Lucknow"),
    (39, "2026-04-27", "19:30", "DC", "RCB", "Delhi"),
    (40, "2026-04-28", "19:30", "PBKS", "RR", "New Chandigarh"),
    (41, "2026-04-29", "19:30", "MI", "SRH", "Mumbai"),
    (42, "2026-04-30", "19:30", "GT", "RCB", "Ahmedabad"),
    (43, "2026-05-01", "19:30", "RR", "DC", "Jaipur"),
    (44, "2026-05-02", "19:30", "CSK", "MI", "Chennai"),
    (45, "2026-05-03", "15:30", "SRH", "KKR", "Hyderabad"),
    (46, "2026-05-03", "19:30", "GT", "PBKS", "Ahmedabad"),
    (47, "2026-05-04", "19:30", "MI", "LSG", "Mumbai"),
    (48, "2026-05-05", "19:30", "DC", "CSK", "Delhi"),
    (49, "2026-05-06", "19:30", "SRH", "PBKS", "Hyderabad"),
    (50, "2026-05-07", "19:30", "LSG", "RCB", "Lucknow"),
    (51, "2026-05-08", "19:30", "DC", "KKR", "Delhi"),
    (52, "2026-05-09", "19:30", "RR", "GT", "Jaipur"),
    (53, "2026-05-10", "15:30", "CSK", "LSG", "Chennai"),
    (54, "2026-05-10", "19:30", "RCB", "MI", "Raipur"),
    (55, "2026-05-11", "19:30", "PBKS", "DC", "Dharamsala"),
    (56, "2026-05-12", "19:30", "GT", "SRH", "Ahmedabad"),
    (57, "2026-05-13", "19:30", "RCB", "KKR", "Raipur"),
    (58, "2026-05-14", "19:30", "PBKS", "MI", "Dharamsala"),
    (59, "2026-05-15", "19:30", "LSG", "CSK", "Lucknow"),
    (60, "2026-05-16", "19:30", "KKR", "GT", "Kolkata"),
    (61, "2026-05-17", "15:30", "PBKS", "RCB", "Dharamsala"),
    (62, "2026-05-17", "19:30", "DC", "RR", "Delhi"),
    (63, "2026-05-18", "19:30", "CSK", "SRH", "Chennai"),
    (64, "2026-05-19", "19:30", "RR", "LSG", "Jaipur"),
    (65, "2026-05-20", "19:30", "KKR", "MI", "Kolkata"),
    (66, "2026-05-21", "19:30", "CSK", "GT", "Ahmedabad"),
    (67, "2026-05-22", "19:30", "SRH", "RCB", "Hyderabad"),
    (68, "2026-05-23", "19:30", "LSG", "PBKS", "Lucknow"),
    (69, "2026-05-24", "15:30", "MI", "RR", "Mumbai"),
    (70, "2026-05-24", "19:30", "KKR", "DC", "Kolkata"),
)


@dataclass(frozen=True)
class Fixture:
    id: int
    match_desc: str
    series_name: str
    team_a: str
    team_b: str
    venue: str
    date: str
    time_ist: str


@dataclass(frozen=True)
class NewsItem:
    id: int
    headline: str
    intro: str
    context: str


@dataclass(frozen=True)
class NewsDetail:
    id: int
    headline: str
    content: list[str]


def _team_name(short_name: str, valid_teams: tuple[str, ...]) -> str:
    full_name = TEAM_NAMES[short_name]
    if full_name == "Royal Challengers Bengaluru" and full_name not in valid_teams:
        return "Royal Challengers Bangalore"
    return full_name


def get_fixtures(valid_teams: tuple[str, ...]) -> list[Fixture]:
    fixtures = [
        Fixture(
            id=match_no,
            match_desc=f"Match {match_no} - {time_ist} IST",
            series_name=TOURNAMENT_NAME,
            team_a=_team_name(team_a, valid_teams),
            team_b=_team_name(team_b, valid_teams),
            venue=VENUE_NAMES.get(venue, venue),
            date=match_date,
            time_ist=time_ist,
        )
        for match_no, match_date, time_ist, team_a, team_b, venue in RAW_FIXTURES
    ]

    today = date.today().isoformat()
    upcoming = [fixture for fixture in fixtures if fixture.date >= today]
    return upcoming or fixtures


def get_news_feed() -> list[NewsItem]:
    return []


def get_news_article(news_id: int) -> NewsDetail | None:
    return None
