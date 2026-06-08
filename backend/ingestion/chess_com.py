import httpx
import asyncio
from datetime import datetime
from typing import AsyncIterator

BASE_URL = "https://api.chess.com/pub/player"
async def fetch_monthly_games(username: str, year: int, month: int) -> list[dict]:
    url = f"{BASE_URL}/{username}/games/{year}/{month:02d}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"User-Agent": "chess-coach-app/1.0"})
        resp.raise_for_status()
        return resp.json().get("games", [])

async def fetch_all_games(username: str, since_year: int = 2023) -> AsyncIterator[dict]:
    """Yield all games since a given year, month by month."""
    now = datetime.now()
    for year in range(since_year, now.year + 1):
        for month in range(1, 13):
            if year == now.year and month > now.month:
                break
            games = await fetch_monthly_games(username, year, month)
            for game in games:
                yield game
            await asyncio.sleep(0.5)  # Be a good API citizen
