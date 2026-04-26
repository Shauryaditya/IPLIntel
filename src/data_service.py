from __future__ import annotations

import csv
import gzip
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parents[1] / "IPL.csv.gz"


@dataclass(frozen=True)
class MatchRecord:
    match_id: str
    season: str
    team_a: str
    team_b: str
    winner: str
    venue: str
    city: str
    toss_winner: str
    toss_decision: str


@dataclass(frozen=True)
class DataBundle:
    matches: tuple[MatchRecord, ...]
    teams: tuple[str, ...]
    venues: tuple[str, ...]
    cities: tuple[str, ...]
    seasons: tuple[str, ...]


def _clean(value: str | None) -> str:
    value = (value or "").strip()
    return "" if value in {"NA", "Unknown", "nan"} else value


@lru_cache(maxsize=1)
def load_data() -> DataBundle:
    matches_by_id: dict[str, dict[str, str | set[str]]] = {}

    with gzip.open(DATA_PATH, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            match_id = _clean(row.get("match_id"))
            if not match_id:
                continue

            item = matches_by_id.setdefault(
                match_id,
                {
                    "match_id": match_id,
                    "season": _clean(row.get("season")),
                    "winner": _clean(row.get("match_won_by")),
                    "venue": _clean(row.get("venue")),
                    "city": _clean(row.get("city")),
                    "toss_winner": _clean(row.get("toss_winner")),
                    "toss_decision": _clean(row.get("toss_decision")),
                    "teams": set(),
                },
            )
            batting_team = _clean(row.get("batting_team"))
            bowling_team = _clean(row.get("bowling_team"))
            if batting_team:
                item["teams"].add(batting_team)  # type: ignore[union-attr]
            if bowling_team:
                item["teams"].add(bowling_team)  # type: ignore[union-attr]

    records: list[MatchRecord] = []
    teams: set[str] = set()
    venues: set[str] = set()
    cities: set[str] = set()
    seasons: set[str] = set()

    for item in matches_by_id.values():
        match_teams = sorted(item["teams"])  # type: ignore[arg-type]
        if len(match_teams) < 2:
            continue
        team_a, team_b = match_teams[:2]
        winner = str(item["winner"])
        if not winner or winner not in match_teams:
            continue

        record = MatchRecord(
            match_id=str(item["match_id"]),
            season=str(item["season"]),
            team_a=team_a,
            team_b=team_b,
            winner=winner,
            venue=str(item["venue"]),
            city=str(item["city"]),
            toss_winner=str(item["toss_winner"]),
            toss_decision=str(item["toss_decision"]),
        )
        records.append(record)
        teams.update(match_teams)
        if record.venue:
            venues.add(record.venue)
        if record.city:
            cities.add(record.city)
        if record.season:
            seasons.add(record.season)

    return DataBundle(
        matches=tuple(records),
        teams=tuple(sorted(teams)),
        venues=tuple(sorted(venues)),
        cities=tuple(sorted(cities)),
        seasons=tuple(sorted(seasons)),
    )


def team_summary(team: str) -> dict[str, float | int]:
    bundle = load_data()
    played = won = 0
    for match in bundle.matches:
        if team in {match.team_a, match.team_b}:
            played += 1
            won += int(match.winner == team)
    return {
        "played": played,
        "won": won,
        "win_rate": round((won / played) * 100, 1) if played else 0,
    }


def head_to_head(team_a: str, team_b: str) -> Counter[str]:
    bundle = load_data()
    counts: Counter[str] = Counter()
    for match in bundle.matches:
        if {team_a, team_b}.issubset({match.team_a, match.team_b}):
            counts[match.winner] += 1
    return counts


def venue_results(venue: str) -> Counter[str]:
    bundle = load_data()
    counts: Counter[str] = Counter()
    for match in bundle.matches:
        if match.venue == venue:
            counts[match.winner] += 1
    return counts


def recent_form(team: str, limit: int = 8) -> list[str]:
    bundle = load_data()
    results: list[str] = []
    for match in reversed(bundle.matches):
        if team in {match.team_a, match.team_b}:
            results.append("W" if match.winner == team else "L")
        if len(results) == limit:
            break
    return results


def season_table() -> dict[str, Counter[str]]:
    bundle = load_data()
    table: dict[str, Counter[str]] = defaultdict(Counter)
    for match in bundle.matches:
        if match.season:
            table[match.season][match.winner] += 1
    return dict(table)
