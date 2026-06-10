import asyncio
import chess
import chess.engine
from pathlib import Path

STOCKFISH_PATH = "/usr/local/bin/stockfish" 
ANALYSIS_DEPTH = 15  # Depth 15 is fast and strong enough for blunder detection

async def analyze_position(engine: chess.engine.UciProtocol, fen: str, move_played: str) -> dict:
    board = chess.Board(fen)

    # Get best move and evaluation
    result = await engine.analyse(board, chess.engine.Limit(depth=ANALYSIS_DEPTH))
    best_move = result.get("pv", [None])[0]
    score = result["score"].relative

    # Now evaluate the move that was actually played
    board_after_played = chess.Board(fen)
    board_after_played.push(chess.Move.from_uci(move_played))
    result_after = await engine.analyse(board_after_played, chess.engine.Limit(depth=ANALYSIS_DEPTH))

    score_after = result_after["score"].relative.negate()  # Negate because it's opponent's turn
    best_cp = score.score(mate_score=10000) or 0
    played_cp = score_after.score(mate_score=10000) or 0
    centipawn_loss = max(0, best_cp - played_cp)

    return {
        "best_move": best_move.uci() if best_move else None,
        "centipawn_loss": centipawn_loss,
        "classification": classify_move(centipawn_loss),
    }

def classify_move(cp_loss: float) -> str:
    if cp_loss < 10:    return "best"
    if cp_loss < 25:    return "good"
    if cp_loss < 50:    return "inaccuracy"
    if cp_loss < 150:   return "mistake"
    return "blunder"


async def analyze_game_batch(game_positions: list[dict], fen_cache: dict) -> list[dict]:

    """
    Analyze a list of positions with FEN-level caching.

    fen_cache: {fen+move_played -> analysis_result} — pre-loaded from DB.
    """

    results = []
    transport, engine = await chess.engine.popen_uci(STOCKFISH_PATH)
    try:
        for pos in game_positions:
            cache_key = f"{pos['fen']}|{pos['move_played']}"
            if cache_key in fen_cache:
                results.append(fen_cache[cache_key])  # Cache hit — skip engine call
                continue
            analysis = await analyze_position(engine, pos["fen"], pos["move_played"])
            fen_cache[cache_key] = analysis
            results.append(analysis)

    finally:
        await engine.quit()
        
    return results
