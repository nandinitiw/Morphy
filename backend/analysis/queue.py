import asyncio
from collections import deque

from sqlalchemy.orm import Session

from analysis.pipeline import process_game
from analysis.stockfish_worker import stockfish_pool


class AnalysisQueue:
    def __init__(self):
        self._queue: deque[str] = deque()
        self._running = False

    def enqueue(self, game_id: str):
        self._queue.append(game_id)

    def enqueue_many(self, game_ids: list[str]):
        self._queue.extend(game_ids)

    async def run_forever(self, db_session_factory, fen_cache: dict | None = None):
        self._running = True
        fen_cache = fen_cache or {}

        while self._running:
            if self._queue:
                game_id = self._queue.popleft()
                db = db_session_factory()
                try:
                    engine = await stockfish_pool.get_engine()
                    await process_game(game_id, db, fen_cache, engine)
                finally:
                    db.close()
            else:
                await asyncio.sleep(2)

    def stop(self):
        self._running = False


analysis_queue = AnalysisQueue()
