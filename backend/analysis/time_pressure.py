import numpy as np
from sklearn.linear_model import LogisticRegression
from db.models import Position, Game
from sqlalchemy.orm import Session

def fit_time_pressure_model(username: str, db: Session) -> dict:
    """
    Fit a logistic regression model: does clock time predict blunder rate?
    Returns model coefficients and key insight thresholds.
    """

    positions = db.query(Position).join(Game).filter(
        Game.username == username,
        Position.is_your_move == True,
        Position.clock_remaining != None,

    ).all()

    if len(positions) < 50:
        return {"error": "Not enough data yet"}

    X = np.array([[p.clock_remaining] for p in positions])
    y = np.array([1 if p.classification == "blunder" else 0 for p in positions])
    model = LogisticRegression()
    model.fit(X, y)

    # Find the clock threshold where blunder probability exceeds 20%

    thresholds = np.linspace(0, 300, 300)
    probs = model.predict_proba(thresholds.reshape(-1, 1))[:, 1]
    critical_threshold = thresholds[np.argmax(probs > 0.20)]

    # Compute actual blunder rates in buckets

    buckets = {"0-15s": [], "15-30s": [], "30-60s": [], "60s+": []}

    for pos in positions:
        t = pos.clock_remaining
        bucket = "0-15s" if t < 15 else "15-30s" if t < 30 else "30-60s" if t < 60 else "60s+"
        buckets[bucket].append(1 if pos.classification == "blunder" else 0)

    blunder_rates = {k: np.mean(v) if v else 0 for k, v in buckets.items()}

    return {
        "critical_threshold_seconds": round(critical_threshold),
        "blunder_rates_by_time": blunder_rates,
        "insight": f"Your blunder rate rises sharply when under {round(critical_threshold)}s on the clock.",
    }
