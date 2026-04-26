from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .predictor import MatchFeatures


MODEL_PATH = Path(__file__).resolve().parents[1] / "ipl_model_v1.pth"


@dataclass(frozen=True)
class ModelPrediction:
    predicted_winner: str
    team_a_probability: float
    confidence: float
    source: str
    reasons: tuple[str, ...] = ()


def _clamp(value: float, low: float = 0.01, high: float = 0.99) -> float:
    return max(low, min(high, value))


@lru_cache(maxsize=1)
def _load_model():
    try:
        import torch
        from torch import nn
    except ImportError:
        return None

    if not MODEL_PATH.exists():
        return None

    checkpoint = torch.load(MODEL_PATH, map_location="cpu")
    if not isinstance(checkpoint, dict):
        return None

    team_count, team_dim = checkpoint["team_emb.weight"].shape
    venue_count, venue_dim = checkpoint["venue_emb.weight"].shape

    class IPLNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.team_emb = nn.Embedding(team_count, team_dim)
            self.venue_emb = nn.Embedding(venue_count, venue_dim)
            self.fc1 = nn.Linear(16, 64)
            self.fc2 = nn.Linear(64, 32)
            self.fc3 = nn.Linear(32, 1)
            self.relu = nn.ReLU()

        def forward(self, team_a, team_b, venue):  # noqa: ANN001
            _ = self.venue_emb(venue)
            team_a_emb = self.team_emb(team_a)
            team_b_emb = self.team_emb(team_b)
            x = torch.cat((team_a_emb, team_b_emb), dim=1)
            x = self.relu(self.fc1(x))
            x = self.relu(self.fc2(x))
            return torch.sigmoid(self.fc3(x))

    model = IPLNet()
    model.load_state_dict(checkpoint)
    model.eval()
    return torch, model


def predict_with_model(features: "MatchFeatures") -> ModelPrediction | None:
    """Hook for the PyTorch model exported from Colab.

    A `.pth` file usually stores only weights. To run it, the app also needs the
    exact model class and preprocessing pipeline from the notebook that trained
    it. Paste those pieces here, load `MODEL_PATH`, and return ModelPrediction.
    """
    loaded = _load_model()
    if loaded is None:
        return None

    from .data_service import load_data

    torch, model = loaded
    bundle = load_data()
    team_to_id = {team: index for index, team in enumerate(bundle.teams)}
    venue_to_id = {venue: index for index, venue in enumerate(bundle.venues)}

    if features.team_a not in team_to_id or features.team_b not in team_to_id:
        return None
    venue_id = venue_to_id.get(features.venue, 0)

    team_a = torch.tensor([team_to_id[features.team_a]], dtype=torch.long)
    team_b = torch.tensor([team_to_id[features.team_b]], dtype=torch.long)
    venue = torch.tensor([venue_id], dtype=torch.long)

    with torch.no_grad():
        probability = float(model(team_a, team_b, venue).item())

    probability = _clamp(probability)
    winner = features.team_a if probability >= 0.5 else features.team_b
    confidence = probability if winner == features.team_a else 1 - probability
    return ModelPrediction(
        predicted_winner=winner,
        team_a_probability=round(probability, 3),
        confidence=round(confidence, 3),
        source="PyTorch model with inferred label mapping",
        reasons=(
            "Loaded ipl_model_v1.pth",
            "Team labels inferred from sorted teams in IPL.csv",
            "Add the original Colab encoders here if their order was different",
        ),
    )
