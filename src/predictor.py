from __future__ import annotations

from dataclasses import dataclass

from .data_service import head_to_head, recent_form, team_summary, venue_results
from .model_adapter import ModelPrediction, predict_with_model


@dataclass(frozen=True)
class MatchFeatures:
    team_a: str
    team_b: str
    venue: str
    toss_winner: str
    toss_decision: str


def _clamp(value: float, low: float = 0.05, high: float = 0.95) -> float:
    return max(low, min(high, value))


def _historical_probability(features: MatchFeatures) -> ModelPrediction:
    team_a = features.team_a
    team_b = features.team_b
    score = 0.5
    reasons: list[str] = []

    h2h = head_to_head(team_a, team_b)
    h2h_total = h2h[team_a] + h2h[team_b]
    if h2h_total:
        h2h_rate = h2h[team_a] / h2h_total
        score += (h2h_rate - 0.5) * 0.36
        reasons.append(f"Head-to-head: {team_a} {h2h[team_a]} - {h2h[team_b]} {team_b}")

    a_summary = team_summary(team_a)
    b_summary = team_summary(team_b)
    if a_summary["played"] and b_summary["played"]:
        team_gap = (float(a_summary["win_rate"]) - float(b_summary["win_rate"])) / 100
        score += team_gap * 0.28
        reasons.append(
            f"Overall win rate: {team_a} {a_summary['win_rate']}%, {team_b} {b_summary['win_rate']}%"
        )

    if features.venue:
        venue = venue_results(features.venue)
        venue_total = venue[team_a] + venue[team_b]
        if venue_total:
            venue_rate = venue[team_a] / venue_total
            score += (venue_rate - 0.5) * 0.22
            reasons.append(f"At this venue: {team_a} {venue[team_a]} - {venue[team_b]} {team_b}")

    a_form = recent_form(team_a)
    b_form = recent_form(team_b)
    if a_form and b_form:
        a_recent = a_form.count("W") / len(a_form)
        b_recent = b_form.count("W") / len(b_form)
        score += (a_recent - b_recent) * 0.12
        reasons.append(f"Recent form: {team_a} {''.join(a_form)}, {team_b} {''.join(b_form)}")

    if features.toss_winner == team_a:
        score += 0.025
        reasons.append(f"Toss edge: {team_a} chose to {features.toss_decision or 'bat/field'}")
    elif features.toss_winner == team_b:
        score -= 0.025
        reasons.append(f"Toss edge: {team_b} chose to {features.toss_decision or 'bat/field'}")

    probability_a = _clamp(score)
    winner = team_a if probability_a >= 0.5 else team_b
    confidence = probability_a if winner == team_a else 1 - probability_a
    return ModelPrediction(
        predicted_winner=winner,
        team_a_probability=round(probability_a, 3),
        confidence=round(confidence, 3),
        source="historical fallback",
        reasons=tuple(reasons[:5]),
    )


def predict_match(features: MatchFeatures) -> ModelPrediction:
    model_prediction = predict_with_model(features)
    if model_prediction is not None:
        return model_prediction
    return _historical_probability(features)
