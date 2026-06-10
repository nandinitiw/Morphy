import chess

def classify_tactical_motif(fen: str, move_played: str, best_move: str) -> str | None:

    """
    Given a position where the player blundered, identify what tactical theme
    they missed. Returns a motif label or None if no clear theme.
    """

    board = chess.Board(fen)
    best = chess.Move.from_uci(best_move)

    # Did best move deliver check?
    board_test = board.copy()
    board_test.push(best)

    if board_test.is_checkmate():
        return "missed_mate"

    if board_test.is_check():
        return detect_check_motif(board, best)

    if is_fork(board, best):
        return "missed_fork"

    if creates_pin(board, best):
        return "missed_pin"

    if creates_skewer(board, best):
        return "missed_skewer"

    if captures_hanging_piece(board, best):
        return "missed_hanging_piece"

    if is_king_safety_issue(board, chess.Move.from_uci(move_played)):
        return "king_safety"

    if is_back_rank_threat(board, best):
        return "missed_back_rank"

    return "positional"  # Catch-all for non-tactical errors


def is_fork(board: chess.Board, move: chess.Move) -> bool:
    """Check if a move attacks two or more pieces simultaneously."""

    board_copy = board.copy()
    board_copy.push(move)
    piece = board_copy.piece_at(move.to_square)

    if not piece:
        return False

    attacked_squares = board_copy.attacks(move.to_square)
    valuable_attacked = 0

    for sq in attacked_squares:
        target = board_copy.piece_at(sq)
        if target and target.color != piece.color:
            if target.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                valuable_attacked += 1

    return valuable_attacked >= 2

def is_back_rank_threat(board: chess.Board, move: chess.Move) -> bool:
    """Check if best move threatens a back-rank checkmate."""

    board_copy = board.copy()
    board_copy.push(move)
    opponent_color = not board.turn
    king_sq = board_copy.king(opponent_color)

    if not king_sq:
        return False

    back_rank = 7 if opponent_color == chess.WHITE else 0
    return chess.square_rank(king_sq) == back_rank


def creates_pin(board: chess.Board, move: chess.Move) -> bool:
    """Simplified pin detection — check if move places a slider behind a piece."""

    board_copy = board.copy()
    board_copy.push(move)

    # Check if any of your sliders (Q, R, B) now pin an opponent piece
    your_color = not board.turn  # After the move, it's opponent's turn

    for sq in chess.SQUARES:
        piece = board_copy.piece_at(sq)

        if piece and piece.color == your_color and piece.piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP]:

            if board_copy.is_pinned(not your_color, sq):
                return True

    return False


def detect_check_motif(board: chess.Board, move: chess.Move) -> str:
    """Sub-classify check-delivering moves."""

    board_copy = board.copy()
    board_copy.push(move)

    checkers = board_copy.checkers()
    checker_count = len(checkers)

    if checker_count >= 2:
        return "missed_double_check"

    if not board_copy.is_check():
        return "missed_check"

    # Discovered check: exactly one checker, and it isn't the piece that moved.
    if checker_count == 1 and move.to_square not in checkers:
        return "missed_discovered_check"

    return "missed_check"


def creates_skewer(board: chess.Board, move: chess.Move) -> bool:
    """Check if best move skewers a valuable piece with a higher-value piece behind it."""

    if board.is_capture(move):
        direction = _ray_direction(move.from_square, move.to_square)
        if direction is None:
            return False

        captured = board.piece_at(move.to_square)
        if not captured or captured.color == board.turn:
            return False
        if captured.piece_type not in [chess.QUEEN, chess.ROOK, chess.KING]:
            return False

        behind = _next_square_on_ray(move.to_square, direction)
        while behind is not None:
            behind_piece = board.piece_at(behind)
            if behind_piece:
                return (
                    behind_piece.color != board.turn
                    and behind_piece.piece_type in [chess.QUEEN, chess.KING]
                )
            behind = _next_square_on_ray(behind, direction)
        return False

    board_copy = board.copy()
    board_copy.push(move)
    your_color = board.turn
    opponent_color = not board.turn

    for sq in chess.SQUARES:
        piece = board_copy.piece_at(sq)
        if not piece or piece.color != your_color:
            continue
        if piece.piece_type not in [chess.QUEEN, chess.ROOK, chess.BISHOP]:
            continue

        for attacked_sq in board_copy.attacks(sq):
            target = board_copy.piece_at(attacked_sq)
            if not target or target.color != opponent_color:
                continue
            if target.piece_type not in [chess.QUEEN, chess.ROOK, chess.KING]:
                continue

            direction = _ray_direction(sq, attacked_sq)
            if direction is None:
                continue

            behind = _next_square_on_ray(attacked_sq, direction)
            while behind is not None:
                behind_piece = board_copy.piece_at(behind)
                if behind_piece:
                    if (
                        behind_piece.color == opponent_color
                        and behind_piece.piece_type in [chess.QUEEN, chess.KING]
                    ):
                        return True
                    break
                behind = _next_square_on_ray(behind, direction)

    return False


def captures_hanging_piece(board: chess.Board, move: chess.Move) -> bool:
    """Check if best move wins an undefended opponent piece."""

    if not board.is_capture(move):
        return False

    defenders = board.attackers(not board.turn, move.to_square)
    return len(defenders) == 0


def _ray_direction(from_sq: chess.Square, to_sq: chess.Square) -> tuple[int, int] | None:
    """Return (file_delta, rank_delta) step for a sliding attack, or None."""

    from_file, from_rank = chess.square_file(from_sq), chess.square_rank(from_sq)
    to_file, to_rank = chess.square_file(to_sq), chess.square_rank(to_sq)
    file_delta = to_file - from_file
    rank_delta = to_rank - from_rank

    if file_delta == 0 and rank_delta != 0:
        return (0, 1 if rank_delta > 0 else -1)
    if rank_delta == 0 and file_delta != 0:
        return (1 if file_delta > 0 else -1, 0)
    if abs(file_delta) == abs(rank_delta) and file_delta != 0:
        return (1 if file_delta > 0 else -1, 1 if rank_delta > 0 else -1)

    return None


def _next_square_on_ray(sq: chess.Square, direction: tuple[int, int]) -> chess.Square | None:
    file = chess.square_file(sq) + direction[0]
    rank = chess.square_rank(sq) + direction[1]
    if 0 <= file <= 7 and 0 <= rank <= 7:
        return chess.square(file, rank)
    return None

def is_king_safety_issue(board: chess.Board, move_played: chess.Move) -> bool:
    """Check if the move played left your king more exposed."""

    # Compare king safety score before/after
    # Simple heuristic: count attackers near king after move

    board_after = board.copy()
    board_after.push(move_played)
    your_king = board_after.king(board.turn)

    if not your_king:
        return False

    attacker_count = len(list(board_after.attackers(not board.turn, your_king)))
    return attacker_count >= 2
