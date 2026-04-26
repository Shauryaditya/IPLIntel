from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from .data_service import DATA_PATH


@dataclass(frozen=True)
class VenueProfile:
    venue: str
    matches: int
    first_innings_average: float
    second_innings_average: float
    par_score: float
    chase_win_rate: float


def _safe_rate(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 2) if denominator else 0.0


@lru_cache(maxsize=1)
def ball_data() -> pd.DataFrame:
    usecols = [
        "match_id",
        "season",
        "innings",
        "batting_team",
        "bowling_team",
        "venue",
        "batter",
        "bowler",
        "valid_ball",
        "runs_batter",
        "runs_bowler",
        "runs_total",
        "team_runs",
        "team_wicket",
        "wicket_kind",
        "player_out",
    ]
    df = pd.read_csv(DATA_PATH, usecols=usecols, low_memory=False)
    text_columns = [
        "season",
        "batting_team",
        "bowling_team",
        "venue",
        "batter",
        "bowler",
        "wicket_kind",
        "player_out",
    ]
    for column in text_columns:
        df[column] = df[column].fillna("").astype(str).str.strip()

    numeric_columns = [
        "match_id",
        "innings",
        "valid_ball",
        "runs_batter",
        "runs_bowler",
        "runs_total",
        "team_runs",
        "team_wicket",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0).astype(int)

    return df


@lru_cache(maxsize=1)
def players() -> tuple[str, ...]:
    df = ball_data()
    names = set(df["batter"].dropna().unique()) | set(df["bowler"].dropna().unique())
    return tuple(sorted(name for name in names if name))


@lru_cache(maxsize=1)
def batters(teams: tuple[str, ...] | None = None) -> tuple[str, ...]:
    df = ball_data()
    if teams:
        df = df[df["batting_team"].isin(teams)]
    return tuple(sorted(name for name in df["batter"].dropna().unique() if name))


@lru_cache(maxsize=1)
def bowlers(teams: tuple[str, ...] | None = None) -> tuple[str, ...]:
    df = ball_data()
    if teams:
        df = df[df["bowling_team"].isin(teams)]
    return tuple(sorted(name for name in df["bowler"].dropna().unique() if name))


def batter_yearly_stats(player: str) -> pd.DataFrame:
    df = ball_data()
    player_df = df[df["batter"] == player].copy()
    if player_df.empty:
        return pd.DataFrame()

    player_df["is_legal_ball"] = player_df["valid_ball"] == 1
    player_df["is_four"] = player_df["runs_batter"] == 4
    player_df["is_six"] = player_df["runs_batter"] == 6
    player_df["is_dismissal"] = player_df["player_out"] == player

    grouped = player_df.groupby("season", as_index=False).agg(
        Runs=("runs_batter", "sum"),
        Balls=("is_legal_ball", "sum"),
        Dismissals=("is_dismissal", "sum"),
        Fours=("is_four", "sum"),
        Sixes=("is_six", "sum"),
    )
    grouped["Strike Rate"] = grouped.apply(lambda row: _safe_rate(row["Runs"] * 100, row["Balls"]), axis=1)
    grouped["Average"] = grouped.apply(lambda row: _safe_rate(row["Runs"], row["Dismissals"]), axis=1)
    grouped["Boundaries"] = grouped["Fours"] + grouped["Sixes"]
    return grouped.sort_values("season")


def bowler_yearly_stats(player: str) -> pd.DataFrame:
    df = ball_data()
    player_df = df[df["bowler"] == player].copy()
    if player_df.empty:
        return pd.DataFrame()

    player_df["is_legal_ball"] = player_df["valid_ball"] == 1
    player_df["is_dot"] = (player_df["runs_total"] == 0) & player_df["is_legal_ball"]
    player_df["is_bowler_wicket"] = player_df["player_out"].ne("") & ~player_df["wicket_kind"].isin(
        ["", "run out", "retired hurt", "retired out", "obstructing the field"]
    )

    grouped = player_df.groupby("season", as_index=False).agg(
        Balls=("is_legal_ball", "sum"),
        Runs=("runs_bowler", "sum"),
        Wickets=("is_bowler_wicket", "sum"),
        Dots=("is_dot", "sum"),
    )
    grouped["Overs"] = grouped["Balls"] / 6
    grouped["Economy"] = grouped.apply(lambda row: _safe_rate(row["Runs"], row["Overs"]), axis=1)
    grouped["Average"] = grouped.apply(lambda row: _safe_rate(row["Runs"], row["Wickets"]), axis=1)
    grouped["Dot Ball %"] = grouped.apply(lambda row: _safe_rate(row["Dots"] * 100, row["Balls"]), axis=1)
    return grouped.sort_values("season")


def batter_vs_bowler_stats(batter: str, bowler: str) -> dict[str, float | int]:
    df = ball_data()
    matchup = df[(df["batter"] == batter) & (df["bowler"] == bowler)].copy()
    if matchup.empty:
        return {"runs": 0, "balls": 0, "dismissals": 0, "strike_rate": 0.0, "fours": 0, "sixes": 0}

    balls = int(matchup["valid_ball"].sum())
    runs = int(matchup["runs_batter"].sum())
    dismissals = int((matchup["player_out"] == batter).sum())
    fours = int((matchup["runs_batter"] == 4).sum())
    sixes = int((matchup["runs_batter"] == 6).sum())
    return {
        "runs": runs,
        "balls": balls,
        "dismissals": dismissals,
        "strike_rate": _safe_rate(runs * 100, balls),
        "fours": fours,
        "sixes": sixes,
    }


def batter_vs_pace_spin_stats(player: str) -> pd.DataFrame:
    df = ball_data()
    player_df = df[df["batter"] == player].copy()
    if player_df.empty:
        return pd.DataFrame()

    roles_path = DATA_PATH.parent / "player_roles.csv"
    if not roles_path.exists():
        return pd.DataFrame()
        
    roles_df = pd.read_csv(roles_path)
    
    merged = player_df.merge(roles_df, left_on="bowler", right_on="player", how="left")
    
    valid_roles = ["Pace", "Spin"]
    merged = merged[merged["role"].isin(valid_roles)]

    if merged.empty:
        return pd.DataFrame()

    merged["is_legal_ball"] = merged["valid_ball"] == 1
    merged["is_four"] = merged["runs_batter"] == 4
    merged["is_six"] = merged["runs_batter"] == 6
    merged["is_dismissal"] = merged["player_out"] == player

    grouped = merged.groupby("role", as_index=False).agg(
        Runs=("runs_batter", "sum"),
        Balls=("is_legal_ball", "sum"),
        Dismissals=("is_dismissal", "sum"),
        Fours=("is_four", "sum"),
        Sixes=("is_six", "sum"),
    )
    grouped["Strike Rate"] = grouped.apply(lambda row: _safe_rate(row["Runs"] * 100, row["Balls"]), axis=1)
    return grouped



def venue_profile(venue: str) -> VenueProfile:
    df = ball_data()
    venue_df = df[df["venue"] == venue]
    if venue_df.empty:
        return VenueProfile(venue, 0, 0, 0, 0, 0)

    innings_scores = (
        venue_df.groupby(["match_id", "innings"], as_index=False)
        .agg(score=("team_runs", "max"), batting_team=("batting_team", "last"))
        .sort_values(["match_id", "innings"])
    )
    first_scores = innings_scores[innings_scores["innings"] == 1]["score"]
    second_scores = innings_scores[innings_scores["innings"] == 2]["score"]

    first_by_match = innings_scores[innings_scores["innings"] == 1].set_index("match_id")
    second_by_match = innings_scores[innings_scores["innings"] == 2].set_index("match_id")
    common_matches = first_by_match.index.intersection(second_by_match.index)
    chase_wins = 0
    for match_id in common_matches:
        if second_by_match.loc[match_id, "score"] > first_by_match.loc[match_id, "score"]:
            chase_wins += 1

    return VenueProfile(
        venue=venue,
        matches=int(venue_df["match_id"].nunique()),
        first_innings_average=round(float(first_scores.mean()), 1) if not first_scores.empty else 0,
        second_innings_average=round(float(second_scores.mean()), 1) if not second_scores.empty else 0,
        par_score=round(float(first_scores.quantile(0.6)), 1) if not first_scores.empty else 0,
        chase_win_rate=round((chase_wins / len(common_matches)) * 100, 1) if len(common_matches) else 0,
    )


def venue_score_distribution(venue: str) -> pd.DataFrame:
    df = ball_data()
    venue_df = df[df["venue"] == venue]
    if venue_df.empty:
        return pd.DataFrame()

    return (
        venue_df.groupby(["match_id", "innings"], as_index=False)
        .agg(Score=("team_runs", "max"), Team=("batting_team", "last"), Season=("season", "last"))
        .sort_values(["Season", "match_id", "innings"])
    )


def top_batters(limit: int = 15) -> pd.DataFrame:
    df = ball_data()
    grouped = df.groupby("batter", as_index=False).agg(Runs=("runs_batter", "sum"), Balls=("valid_ball", "sum"))
    grouped["Strike Rate"] = grouped.apply(lambda row: _safe_rate(row["Runs"] * 100, row["Balls"]), axis=1)
    return grouped.sort_values("Runs", ascending=False).head(limit).rename(columns={"batter": "Player"})


def top_bowlers(limit: int = 15) -> pd.DataFrame:
    df = ball_data().copy()
    df["is_bowler_wicket"] = df["player_out"].ne("") & ~df["wicket_kind"].isin(
        ["", "run out", "retired hurt", "retired out", "obstructing the field"]
    )
    grouped = df.groupby("bowler", as_index=False).agg(Wickets=("is_bowler_wicket", "sum"), Runs=("runs_bowler", "sum"))
    return grouped.sort_values("Wickets", ascending=False).head(limit).rename(columns={"bowler": "Player"})
