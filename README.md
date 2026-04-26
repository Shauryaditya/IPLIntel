# IPL Match Predictor

A starter platform for turning the Colab IPL prediction model into a usable app.

## What is included

- Match prediction screen
- Head-to-head and venue-aware probability fallback
- Player analytics over IPL seasons
- Batter-vs-bowler matchup statistics
- Venue score profile with par score and chase rate
- Team and venue insights from `IPL.csv`
- Optional PyTorch model adapter for `ipl_model_v1.pth`

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Connecting the Colab model

The app can already make a reasonable data-backed prediction from historical win rates. To use your actual `.pth` model, copy the model architecture and preprocessing code from Colab into `src/model_adapter.py`.

The important function is:

```python
predict_with_model(features: MatchFeatures) -> ModelPrediction | None
```

Return `None` while the PyTorch model is not fully wired; the app will keep using the fallback predictor.

## Analytics Roadmap

The first analytics layer is in `src/stats_service.py`. It currently supports:

- batter yearly runs, strike rate, average, fours, and sixes
- bowler yearly wickets, economy, average, and dot-ball percentage
- batter-vs-bowler matchup stats
- venue first-innings average, second-innings average, par score, and chase win rate

For pace-vs-spin analysis, add a bowler classification file such as `data/player_roles.csv` with columns like:

```csv
player,bowling_type
JJ Bumrah,pace
R Ashwin,spin
Rashid Khan,spin
```
