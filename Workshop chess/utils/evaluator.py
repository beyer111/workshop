"""
评估函数模块
"""
from typing import Dict
from game.board import Board
from game.pieces import Piece, PieceType
from game.rules import Rules


class Evaluator:
    """局面评估器"""
    
    # 位置价值表（简化版，实际可以更精细）
    POSITION_TABLES: Dict[PieceType, Dict[tuple, int]] = {}
    
    @staticmethod
    def init_position_tables():
        """初始化位置价值表"""
        # 将/帅：中心位置更安全
        king_table = {}
        for row in range(10):
            for col in range(9):
                if 3 <= col <= 5:
                    if (0 <= row <= 2) or (7 <= row <= 9):
                        king_table[(row, col)] = 10
                    else:
                        king_table[(row, col)] = 0
                else:
                    king_table[(row, col)] = 0
        Evaluator.POSITION_TABLES[PieceType.KING] = king_table
        
        # 车：控制中心线和底线
        rook_table = {}
        for row in range(10):
            for col in range(9):
                value = 0
                if col == 4:  # 中心线
                    value += 5
                if row == 0 or row == 9:  # 底线
                    value += 3
                rook_table[(row, col)] = value
        Evaluator.POSITION_TABLES[PieceType.ROOK] = rook_table
        
        # 炮：中心位置更灵活
        cannon_table = {}
        for row in range(10):
            for col in range(9):
                value = 0
                if 2 <= row <= 7 and 2 <= col <= 6:
                    value += 3
                cannon_table[(row, col)] = value
        Evaluator.POSITION_TABLES[PieceType.CANNON] = cannon_table
        
        # 马：中心位置更灵活
        horse_table = {}
        for row in range(10):
            for col in range(9):
                value = 0
                if 2 <= row <= 7 and 2 <= col <= 6:
                    value += 2
                horse_table[(row, col)] = value
        Evaluator.POSITION_TABLES[PieceType.HORSE] = horse_table
        
        # 其他棋子使用默认值
        for piece_type in [PieceType.ELEPHANT, PieceType.ADVISOR, PieceType.PAWN]:
            Evaluator.POSITION_TABLES[piece_type] = {}
            for row in range(10):
                for col in range(9):
                    Evaluator.POSITION_TABLES[piece_type][(row, col)] = 0
    
    @staticmethod
    def evaluate(board: Board, is_red: bool, use_position: bool = True) -> int:
        """
        评估局面
        
        Args:
            board: 棋盘
            is_red: 评估方是否为红方
            use_position: 是否使用位置价值
        
        Returns:
            评估分数（正数表示评估方优势）
        """
        if not Evaluator.POSITION_TABLES:
            Evaluator.init_position_tables()
        
        material_score = 0
        position_score = 0
        king_safety = 0
        mobility_score = 0
        
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece:
                    value = piece.get_value()
                    if piece.is_red == is_red:
                        material_score += value
                        if use_position and piece.piece_type in Evaluator.POSITION_TABLES:
                            pos_table = Evaluator.POSITION_TABLES[piece.piece_type]
                            position_score += pos_table.get((row, col), 0)
                        king_safety += Evaluator._king_safety_bonus(board, piece, is_red)
                        mobility_score += Evaluator._mobility(board, piece)
                    else:
                        material_score -= value
                        if use_position and piece.piece_type in Evaluator.POSITION_TABLES:
                            pos_table = Evaluator.POSITION_TABLES[piece.piece_type]
                            position_score -= pos_table.get((row, col), 0)
                        king_safety -= Evaluator._king_safety_bonus(board, piece, not is_red)
                        mobility_score -= Evaluator._mobility(board, piece)
        
        return material_score + position_score + king_safety + mobility_score
    
    @staticmethod
    def _king_safety_bonus(board: Board, piece: Piece, is_red: bool) -> int:
        """根据将/帅安全和周围保护加分"""
        if piece.piece_type != PieceType.KING:
            return 0
        
        # 将在九宫内且未被炮/车直线瞄准时加分
        safety = 0
        row, col = piece.row, piece.col
        if board.is_in_palace(row, col, is_red):
            safety += 20
        
        # 周围友方棋子数量
        defenders = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < Board.ROWS and 0 <= c < Board.COLS:
                    neighbor = board.get_piece(r, c)
                    if neighbor and neighbor.is_red == is_red:
                        defenders += 1
        safety += defenders * 5
        return safety
    
    @staticmethod
    def _mobility(board: Board, piece: Piece) -> int:
        """简单机动性：棋子合法走法越多，越有利"""
        # 确保 Rules 可用
        from game.rules import Rules
        moves = Rules.get_legal_moves(board, piece)
        value = len(moves)
        if piece.piece_type == PieceType.ROOK:
            value *= 2
        elif piece.piece_type == PieceType.CANNON:
            value = int(value * 1.5)
        return value


# 初始化位置表
Evaluator.init_position_tables()

