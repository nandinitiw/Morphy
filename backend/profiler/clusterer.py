import numpy as np
from sklearn.cluster import HDBSCAN
from sklearn.preprocessing import StandardScaler
from db.models import Game, Position, WeaknessProfile
from datetime import datetime

THEME_LABELS = {
    "missed_fork": "Fork Blindspot",
    "missed_pin": "Pin Recognition",
    "missed_back_rank": "Back-Rank Awareness",
    "king_safety": "King Safety",
    "missed_check": "Missed Checks",
    "positional": "Positional Judgment",
}

def update_weakness_profile(username: str, blunder_positions: list[Position], db) -> list[WeaknessProfile]:
    """
    Re-cluster all blunders and update the weakness profile.
    Called after each new batch of analyzed games.
    """

    if not blunder_positions:
        return []
    # Group by tactical motif first, then cluster within each group
    motif_groups = {}
    for pos in blunder_positions:
        motif = pos.tactical_motif or "positional"
        motif_groups.setdefault(motif, []).append(pos)
    profiles = []

    for motif, positions in motif_groups.items():
        embeddings = np.array([pos.embedding for pos in positions])

        if len(embeddings) < 3:
            # Not enough data to cluster — just record it
            profile = _upsert_profile(username, motif, positions, None, db)
            profiles.append(profile)
            continue

        scaler = StandardScaler()
        embeddings_scaled = scaler.fit_transform(embeddings)

        # HDBSCAN: doesn't require specifying k, handles noise

        clusterer = HDBSCAN(min_cluster_size=3, min_samples=2)
        labels = clusterer.fit_predict(embeddings_scaled)
        centroid = embeddings_scaled.mean(axis=0).tolist()
        profile = _upsert_profile(username, motif, positions, centroid, db)
        profiles.append(profile)

    db.commit()
    return profiles


def refresh_weakness_profile(username: str, db) -> list[WeaknessProfile]:
    blunders = (
        db.query(Position)
        .join(Game)
        .filter(
            Game.username == username,
            Position.is_your_move.is_(True),
            Position.classification == "blunder",
        )
        .all()
    )
    return update_weakness_profile(username, blunders, db)


def _upsert_profile(username, motif, positions, centroid, db) -> WeaknessProfile:

    existing = db.query(WeaknessProfile).filter_by(username=username, theme=motif).first()
    avg_cp_loss = np.mean([p.centipawn_loss for p in positions if p.centipawn_loss])

    if existing:
        existing.frequency = len(positions)
        existing.severity = float(avg_cp_loss)
        existing.last_seen = max(p.game.played_at for p in positions)
        existing.centroid = centroid
        existing.updated_at = datetime.now()

        return existing

    else:
        profile = WeaknessProfile(
            username=username,
            theme=motif,
            frequency=len(positions),
            severity=float(avg_cp_loss),
            last_seen=datetime.now(),
            centroid=centroid,
            updated_at=datetime.now(),

        )

        db.add(profile)
        return profile
