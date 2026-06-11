import asyncio
import os

import chess
import chess.engine
from sqlalchemy.orm import Session

from db.models import Position

STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/local/bin/stockfish")
ANALYSIS_DEPTH = int(os.getenv("ANALYSIS_DEPTH", "15"))

SKIPPED_RESULT = {"best_move": None, "centipawn_loss": None, "classification": None}


class StockfishPool:
    def __init__(self):
        self._engine = None
        self._lock = asyncio.Lock()

    async def get_engine(self):
        async with self._lock:
            if self._engine is None:
                _, self._engine = await chess.engine.popen_uci(STOCKFISH_PATH)
            return self._engine

    async def close(self):
        async with self._lock:
            if self._engine is not None:
                await self._engine.quit()
                self._engine = None


stockfish_pool = StockfishPool()


def load_fen_cache_from_db(db: Session) -> dict:
    cache = {}
    rows = db.query(Position).filter(Position.best_move.isnot(None)).all()
    for position in rows:
        key = f"{position.fen}|{position.move_played}"
        cache[key] = {
            "best_move": position.best_move,
            "centipawn_loss": position.centipawn_loss,
            "classification": position.classification,
        }
    return cache


async def analyze_position(engine: chess.engine.UciProtocol, fen: str, move_played: str) -> dict:
    board = chess.Board(fen)

    result = await engine.analyse(board, chess.engine.Limit(depth=ANALYSIS_DEPTH))
    best_move = result.get("pv", [None])[0]
    score = result["score"].relative

    board_after_played = chess.Board(fen)
    board_after_played.push(chess.Move.from_uci(move_played))
    result_after = await engine.analyse(board_after_played, chess.engine.Limit(depth=ANALYSIS_DEPTH))

    score_after = result_after["score"].relative.negate()
    best_cp = score.score(mate_score=10000) or 0
    played_cp = score_after.score(mate_score=10000) or 0
    centipawn_loss = max(0, best_cp - played_cp)

    return {
        "best_move": best_move.uci() if best_move else None,
        "centipawn_loss": centipawn_loss,
        "classification": classify_move(centipawn_loss),
    }


def classify_move(cp_loss: float) -> str:
    if cp_loss < 10:
        return "best"
    if cp_loss < 25:
        return "good"
    if cp_loss < 50:
        return "inaccuracy"
    if cp_loss < 150:
        return "mistake"
    return "blunder"


async def analyze_game_batch_with_engine(
    engine: chess.engine.UciProtocol,
    game_positions: list[dict],
    fen_cache: dict,
) -> list[dict]:
    results = []
    for pos in game_positions:
        if not pos.get("analyze", True):
            results.append(SKIPPED_RESULT.copy())
            continue

        cache_key = f"{pos['fen']}|{pos['move_played']}"
        if cache_key in fen_cache:
            results.append(fen_cache[cache_key])
            continue

        analysis = await analyze_position(engine, pos["fen"], pos["move_played"])
        fen_cache[cache_key] = analysis
        results.append(analysis)

    return results


async def analyze_game_batch(game_positions: list[dict], fen_cache: dict) -> list[dict]:
    engine = await stockfish_pool.get_engine()
    return await analyze_game_batch_with_engine(engine, game_positions, fen_cache)
