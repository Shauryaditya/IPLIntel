from __future__ import annotations

import streamlit as st

from src.data_service import head_to_head, load_data, recent_form, season_table, team_summary, venue_results
from src.live_service import get_fixtures
from src.predictor import MatchFeatures, predict_match
from src.stats_service import (
    batter_vs_bowler_stats,
    batter_vs_pace_spin_stats,
    batter_yearly_stats,
    batters,
    bowler_yearly_stats,
    bowlers,
    top_batters,
    top_bowlers,
    venue_profile,
    venue_score_distribution,
)


st.set_page_config(page_title="IPL Match Predictor", page_icon="IP", layout="wide")


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


@st.cache_data(show_spinner=False)
def get_bundle():
    return load_data()


bundle = get_bundle()

st.title("IPL Match Predictor")

if "selected_match" not in st.session_state:
    st.session_state.selected_match = None

if st.session_state.selected_match is None:
    st.subheader("Upcoming Fixtures")
    fixtures = get_fixtures(tuple(bundle.teams))
    if not fixtures:
        st.info("No fixtures matching our historical dataset.")
    else:
        for f in fixtures:
            with st.container(border=True):
                st.write(f"**{f.team_a} vs {f.team_b}**")
                st.caption(f"{f.date} at {f.time_ist} IST - {f.venue}")
                if st.button("Analyze", key=f"btn_{f.id}", use_container_width=True):
                    st.session_state.selected_match = {
                        "team_a": f.team_a,
                        "team_b": f.team_b,
                        "venue": f.venue,
                    }
                    st.rerun()

    st.stop()

if st.button("Back to Fixtures"):
    st.session_state.selected_match = None
    st.rerun()

tabs = st.tabs(["Predict", "Analytics", "Matchups", "Teams", "Venues", "Seasons"])

with tabs[0]:
    left, right = st.columns([1.1, 0.9], gap="large")

    with left:
        st.subheader("Match Setup")
        sm = st.session_state.selected_match
        idx_a = bundle.teams.index(sm["team_a"]) if sm["team_a"] in bundle.teams else 0
        team_a = st.selectbox("Team A", bundle.teams, index=idx_a)

        team_b_options = [team for team in bundle.teams if team != team_a]
        idx_b = team_b_options.index(sm["team_b"]) if sm["team_b"] in team_b_options else 0
        team_b = st.selectbox("Team B", team_b_options, index=idx_b)

        venues_list = [""] + list(bundle.venues)
        best_idx = 0
        v_lower = sm["venue"].lower()
        for i, v in enumerate(venues_list):
            if v and (v.lower() in v_lower or v_lower in v.lower()):
                best_idx = i
                break

        venue = st.selectbox("Venue", venues_list, index=best_idx)
        toss_winner = st.selectbox("Toss Winner", [""] + [team_a, team_b])
        toss_decision = st.radio("Toss Decision", ["bat", "field"], horizontal=True)

    features = MatchFeatures(
        team_a=team_a,
        team_b=team_b,
        venue=venue,
        toss_winner=toss_winner,
        toss_decision=toss_decision or "",
    )
    prediction = predict_match(features)

    with right:
        st.subheader("Prediction")
        st.metric("Predicted Winner", prediction.predicted_winner)
        st.metric(f"{team_a} Win Probability", percent(prediction.team_a_probability))
        st.metric("Confidence", percent(prediction.confidence))
        st.caption(f"Source: {prediction.source}")

        st.progress(prediction.team_a_probability, text=f"{team_a} vs {team_b}")
        if prediction.reasons:
            st.write("Key signals")
            for reason in prediction.reasons:
                st.write(f"- {reason}")

    st.divider()
    c1, c2, c3 = st.columns(3)
    h2h = head_to_head(team_a, team_b)
    c1.metric(f"{team_a} H2H Wins", h2h[team_a])
    c2.metric(f"{team_b} H2H Wins", h2h[team_b])
    if venue:
        venue_counts = venue_results(venue)
        c3.metric("Venue Matches In Data", sum(venue_counts.values()))
    else:
        c3.metric("Venue Matches In Data", "Select venue")

with tabs[1]:
    st.subheader("Player Performance")
    player_col, metric_col = st.columns([0.8, 1.2], gap="large")

    with player_col:
        current_teams = (team_a, team_b)
        selected_batter = st.selectbox("Batter", batters(current_teams), key="analytics_batter")
        selected_bowler = st.selectbox("Bowler", bowlers(current_teams), key="analytics_bowler")

    batter_stats = batter_yearly_stats(selected_batter)
    bowler_stats = bowler_yearly_stats(selected_bowler)

    with metric_col:
        c1, c2, c3 = st.columns(3)
        c1.metric("Batter Runs", int(batter_stats["Runs"].sum()) if not batter_stats.empty else 0)
        c2.metric(
            "Batter Strike Rate",
            round(float(batter_stats["Runs"].sum() * 100 / batter_stats["Balls"].sum()), 2)
            if not batter_stats.empty and batter_stats["Balls"].sum()
            else 0,
        )
        c3.metric("Bowler Wickets", int(bowler_stats["Wickets"].sum()) if not bowler_stats.empty else 0)

    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.write(f"{selected_batter} batting over seasons")
        if batter_stats.empty:
            st.info("No batting data available for this player.")
        else:
            st.line_chart(batter_stats.set_index("season")[["Runs", "Strike Rate"]])
            st.dataframe(batter_stats, hide_index=True, use_container_width=True)

    with chart_right:
        st.write(f"{selected_bowler} bowling over seasons")
        if bowler_stats.empty:
            st.info("No bowling data available for this player.")
        else:
            st.line_chart(bowler_stats.set_index("season")[["Wickets", "Economy", "Dot Ball %"]])
            st.dataframe(bowler_stats, hide_index=True, use_container_width=True)

    st.divider()

    st.write(f"{selected_batter} vs Pace and Spin")
    pace_spin_stats = batter_vs_pace_spin_stats(selected_batter)
    if pace_spin_stats.empty:
        st.info("No pace/spin data available for this batter. Please ensure bowlers are mapped in player_roles.csv.")
    else:
        ps_left, ps_right = st.columns(2)
        with ps_left:
            st.write("Runs Scored")
            st.bar_chart(pace_spin_stats.set_index("role")["Runs"])
        with ps_right:
            st.write("Strike Rate")
            st.bar_chart(pace_spin_stats.set_index("role")["Strike Rate"])

    st.divider()
    top_left, top_right = st.columns(2, gap="large")
    with top_left:
        st.write("Top run scorers in dataset")
        st.bar_chart(top_batters().set_index("Player")["Runs"])
    with top_right:
        st.write("Top wicket takers in dataset")
        st.bar_chart(top_bowlers().set_index("Player")["Wickets"])

with tabs[2]:
    st.subheader("Matchups And Venue Score")
    match_col, venue_col = st.columns([1, 1], gap="large")

    with match_col:
        current_teams = (team_a, team_b)
        matchup_batter = st.selectbox("Matchup Batter", batters(current_teams), key="matchup_batter")
        matchup_bowler = st.selectbox("Matchup Bowler", bowlers(current_teams), key="matchup_bowler")
        matchup = batter_vs_bowler_stats(matchup_batter, matchup_bowler)
        c1, c2, c3 = st.columns(3)
        c1.metric("Runs", matchup["runs"])
        c2.metric("Balls", matchup["balls"])
        c3.metric("Dismissals", matchup["dismissals"])
        c4, c5, c6 = st.columns(3)
        c4.metric("Strike Rate", matchup["strike_rate"])
        c5.metric("Fours", matchup["fours"])
        c6.metric("Sixes", matchup["sixes"])

    with venue_col:
        score_venue = st.selectbox("Score Venue", bundle.venues, key="score_venue")
        profile = venue_profile(score_venue)
        c1, c2, c3 = st.columns(3)
        c1.metric("Matches", profile.matches)
        c2.metric("Par Score", profile.par_score)
        c3.metric("Chase Win Rate", f"{profile.chase_win_rate}%")
        c4, c5 = st.columns(2)
        c4.metric("1st Inn Avg", profile.first_innings_average)
        c5.metric("2nd Inn Avg", profile.second_innings_average)

    scores = venue_score_distribution(score_venue)
    st.write(f"Scores at {score_venue}")
    if scores.empty:
        st.info("No score data available for this venue.")
    else:
        st.scatter_chart(scores, x="Season", y="Score", color="innings")
        st.dataframe(scores.tail(20), hide_index=True, use_container_width=True)

with tabs[3]:
    st.subheader("Team Insights")
    selected_team = st.selectbox("Team", bundle.teams, key="team_insights")
    summary = team_summary(selected_team)
    form = recent_form(selected_team, limit=10)
    c1, c2, c3 = st.columns(3)
    c1.metric("Matches", summary["played"])
    c2.metric("Wins", summary["won"])
    c3.metric("Win Rate", f"{summary['win_rate']}%")
    st.write("Recent form")
    st.write(" ".join(form) if form else "No recent form available")

with tabs[4]:
    st.subheader("Venue Insights")
    selected_venue = st.selectbox("Venue", bundle.venues, key="venue_insights")
    counts = venue_results(selected_venue)
    rows = [{"Team": team, "Wins": wins} for team, wins in counts.most_common(12)]
    st.dataframe(rows, hide_index=True, use_container_width=True)

with tabs[5]:
    st.subheader("Season Winners In Dataset")
    table = season_table()
    rows = []
    for season, counts in sorted(table.items()):
        winner, wins = counts.most_common(1)[0]
        rows.append({"Season": season, "Most Wins": winner, "Wins": wins})
    st.dataframe(rows, hide_index=True, use_container_width=True)
