"""Shared fixtures: in-memory SQLite DB seeded with known game/position data."""
from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Base, Game, Position, WeaknessProfile, GmProfile


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def make_game(db: Session, *, id: str, username: str = "testuser",
              tc: str = "600+0", result: str = "win",
              color: str = "white", analyzed: bool = True,
              opening: str = "Ruy Lopez", raw_pgn: str | None = None) -> Game:
    g = Game(
        id=id, username=username, player_color=color, result=result,
        time_control=tc, eco="C65", opening_name=opening,
        played_at=datetime(2024, 1, 1), raw_pgn=raw_pgn, analyzed=analyzed,
    )
    db.add(g)
    db.flush()
    return g


def make_blunder(db: Session, *, game_id: str, move: int = 10,
                 motif: str = "missed_fork", cp_loss: float = 300.0,
                 fen: str = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1") -> Position:
    p = Position(
        game_id=game_id, move_number=move, fen=fen,
        move_played="e2e4", best_move="d2d4",
        centipawn_loss=cp_loss, classification="blunder",
        is_your_move=True, tactical_motif=motif,
    )
    db.add(p)
    db.flush()
    return p
