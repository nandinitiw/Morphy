import asyncio
from collections import deque

from backend.analysis.stockfish_worker import analyze_game_batch
from backend.db.models import Game, Position


class AnalysisQueue:
    def __init__(self):
        self._queue = deque()
        self._running = False

    def enqueue(self, game_id: str):
        self._queue.append(game_id)

    async def run_forever(self, db_session, fen_cache):
        self._running = True
        while self._running:
            if self._queue:
                game_id = self._queue.popleft()
                await self._process_game(game_id, db_session, fen_cache)

            else:
                await asyncio.sleep(2)  # Poll every 2s when idle

    async def _process_game(self, game_id: str, db, fen_cache: dict):

        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError(f"Game {game_id} not found")

        positions = (
            db.query(Position)
            .filter(Position.game_id == game_id)
            .order_by(Position.move_number)
            .all()
        )
        position_dicts = [
            {"fen": p.fen, "move_played": p.move_played} for p in positions
        ]

        results = await analyze_game_batch(position_dicts, fen_cache)

        for position, result in zip(positions, results):
            position.best_move = result["best_move"]
            position.centipawn_loss = result["centipawn_loss"]
            position.classification = result["classification"]

        game.analyzed = True
        db.commit()
