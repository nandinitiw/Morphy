from sqlalchemy import func
from sqlalchemy.orm import Session
import httpx

from db.models import Game, Position, WeaknessProfile

TOOLS = [
    {
        "name": "get_recent_games",
        "description": "Fetch the user's most recent analyzed games with their accuracy and result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of recent games to fetch (default 10)"},
            },
        },
    },
    {
        "name": "get_weakness_profile",
        "description": "Get the user's current weakness fingerprint — their persistent tactical and positional blind spots.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_game_details",
        "description": "Get move-by-move analysis for a specific game, including all blunders and missed tactics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "game_id": {"type": "string", "description": "The Chess.com game ID"},
            },
            "required": ["game_id"],
        },
    },
    {
        "name": "get_opening_stats",
        "description": "Get win/loss/draw rates and average accuracy for each opening the user has played.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "fetch_practice_puzzles",
        "description": "Fetch Lichess puzzles targeting a specific weakness theme.",
        "input_schema": {
            "type": "object",
            "properties": {
                "theme": {"type": "string", "description": "Tactical theme e.g. 'fork', 'pin', 'backRankMate'"},
                "limit": {"type": "integer", "default": 5},
            },
            "required": ["theme"],
        },
    },
]


async def execute_tool(tool_name: str, tool_input: dict, username: str, db: Session) -> str:
    try:
        if tool_name == "get_recent_games":
            return _get_recent_games(username, tool_input.get("limit", 10), db)
        if tool_name == "get_weakness_profile":
            return _get_weakness_profile(username, db)
        if tool_name == "get_game_details":
            return _get_game_details(tool_input["game_id"], username, db)
        if tool_name == "get_opening_stats":
            return _get_opening_stats(username, db)
        if tool_name == "fetch_practice_puzzles":
            return await _fetch_puzzles(tool_input["theme"], tool_input.get("limit", 5))
        return f"Unknown tool: {tool_name}"
    except KeyError as exc:
        return f"Tool error ({tool_name}): missing required input {exc.args[0]}"
    except Exception as exc:
        return f"Tool error ({tool_name}): {exc}"


def _get_weakness_profile(username: str, db: Session) -> str:
    profiles = (
        db.query(WeaknessProfile)
        .filter_by(username=username)
        .order_by(WeaknessProfile.severity.desc())
        .all()
    )

    if not profiles:
        return "No weakness profile yet — not enough games analyzed."

    lines = ["Current Weakness Profile:"]
    for profile in profiles:
        last_seen = profile.last_seen.date() if profile.last_seen else "unknown"
        lines.append(
            f"- {profile.theme}: seen {profile.frequency}x, "
            f"avg {profile.severity:.0f} centipawn loss, last seen {last_seen}"
        )
    return "\n".join(lines)


def _get_recent_games(username: str, limit: int, db: Session) -> str:
    games = (
        db.query(Game)
        .filter_by(username=username, analyzed=True)
        .order_by(Game.played_at.desc())
        .limit(limit)
        .all()
    )

    if not games:
        return "No analyzed games yet."

    game_ids = [game.id for game in games]
    blunder_counts = dict(
        db.query(Position.game_id, func.count(Position.id))
        .filter(
            Position.game_id.in_(game_ids),
            Position.is_your_move.is_(True),
            Position.classification == "blunder",
        )
        .group_by(Position.game_id)
        .all()
    )

    lines = [f"Recent {len(games)} games:"]
    for game in games:
        blunders = blunder_counts.get(game.id, 0)
        lines.append(
            f"- {game.id}: {game.result} as {game.player_color}, "
            f"{game.opening_name}, {blunders} blunders"
        )
    return "\n".join(lines)


def _get_game_details(game_id: str, username: str, db: Session) -> str:
    game = db.query(Game).filter_by(id=game_id, username=username).first()
    if not game:
        return f"Game {game_id} not found for user {username}."
    if not game.analyzed:
        return f"Game {game_id} has not been analyzed yet."

    positions = (
        db.query(Position)
        .filter_by(game_id=game_id, is_your_move=True)
        .order_by(Position.move_number)
        .all()
    )

    lines = [
        f"Game {game_id}: {game.result} as {game.player_color}, {game.opening_name}",
        f"Time control: {game.time_control}",
        "",
        "Notable moves:",
    ]

    notable = False
    for position in positions:
        if position.classification not in ("blunder", "mistake", "inaccuracy") and not position.tactical_motif:
            continue
        notable = True
        motif = f", motif: {position.tactical_motif}" if position.tactical_motif else ""
        cp_loss = f"{position.centipawn_loss:.0f}" if position.centipawn_loss is not None else "n/a"
        lines.append(
            f"  Move {position.move_number}: {position.move_played} -> {position.classification} "
            f"(best: {position.best_move}, cp loss: {cp_loss}{motif})"
        )

    if not notable:
        lines.append("  No significant errors flagged.")

    return "\n".join(lines)


def _get_opening_stats(username: str, db: Session) -> str:
    games = db.query(Game).filter_by(username=username, analyzed=True).all()
    if not games:
        return "No analyzed games yet."

    stats: dict[str, dict] = {}
    for game in games:
        opening = game.opening_name or game.eco or "Unknown"
        if opening not in stats:
            stats[opening] = {"win": 0, "loss": 0, "draw": 0, "cp_losses": []}
        stats[opening][game.result] += 1

        cp_losses = [
            position.centipawn_loss
            for position in db.query(Position)
            .filter_by(game_id=game.id, is_your_move=True)
            .filter(Position.centipawn_loss.isnot(None))
            .all()
        ]
        stats[opening]["cp_losses"].extend(cp_losses)

    lines = ["Opening statistics:"]
    for opening, data in sorted(
        stats.items(),
        key=lambda item: item[1]["win"] + item[1]["loss"] + item[1]["draw"],
        reverse=True,
    ):
        total = data["win"] + data["loss"] + data["draw"]
        avg_cp = sum(data["cp_losses"]) / len(data["cp_losses"]) if data["cp_losses"] else 0
        lines.append(
            f"- {opening}: {total} games, W{data['win']}/L{data['loss']}/D{data['draw']}, "
            f"avg cp loss {avg_cp:.0f}"
        )
    return "\n".join(lines)


async def _fetch_puzzles(theme: str, limit: int) -> str:
    url = f"https://lichess.org/api/puzzle/batch?themes={theme}&nb={limit}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            return f"Could not fetch puzzles for theme '{theme}'"

        puzzles = resp.json().get("puzzles", [])
        lines = [f"Practice puzzles for '{theme}':"]

        for puzzle in puzzles:
            lines.append(
                f"- https://lichess.org/training/{puzzle['puzzle']['id']} "
                f"(rating: {puzzle['puzzle']['rating']})"
            )

        return "\n".join(lines)
