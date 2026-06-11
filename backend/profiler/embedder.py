import chess
import numpy as np

PIECE_VALUES = {
    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
}

def fen_to_vector(fen: str) -> list[float]:

    """

    Convert a FEN string to a fixed-length feature vector.

    

    Features:

    - Material balance (per piece type)

    - Piece mobility

    - King safety proxies

    - Pawn structure features

    - Game phase indicator

    """

    board = chess.Board(fen)
    features = []

    # 1. Material counts per piece type (12 features: 6 piece types × 2 colors)
    for color in [chess.WHITE, chess.BLACK]:
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
            features.append(len(board.pieces(piece_type, color)))

    # 2. Material balance (1 feature)
    material_balance = sum(
        PIECE_VALUES[pt] * (len(board.pieces(pt, chess.WHITE)) - len(board.pieces(pt, chess.BLACK)))
        for pt in PIECE_VALUES
    )

    features.append(material_balance / 39.0)  # Normalize by max material
    # 3. Mobility — number of legal moves (1 feature, normalized)
    features.append(board.legal_moves.count() / 50.0)

    # 4. King safety: attackers near each king (2 features)
    for color in [chess.WHITE, chess.BLACK]:
        king_sq = board.king(color)
        if king_sq:
            attackers = len(list(board.attackers(not color, king_sq)))
            features.append(attackers / 8.0)
        else:
            features.append(0.0)

    # 5. Game phase: total material remaining (1 feature, normalized)

    total_material = sum(
        PIECE_VALUES[pt] * (len(board.pieces(pt, chess.WHITE)) + len(board.pieces(pt, chess.BLACK)))
        for pt in PIECE_VALUES if pt != chess.KING
    )

    features.append(total_material / 78.0)  # Max starting material
    # 6. Pawn structure: doubled, isolated pawns (4 features)
    for color in [chess.WHITE, chess.BLACK]:
        pawns = board.pieces(chess.PAWN, color)
        files = [chess.square_file(sq) for sq in pawns]
        doubled = sum(1 for f in set(files) if files.count(f) > 1)
        isolated = sum(1 for f in files if (f - 1) not in files and (f + 1) not in files)
        features.extend([doubled / 8.0, isolated / 8.0])

    return features  # ~22-dimensional vector

