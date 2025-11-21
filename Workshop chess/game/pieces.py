"""
中国象棋棋子类定义
"""
from enum import Enum


class PieceType(Enum):
    """棋子类型"""
    KING = "将"      # 将/帅
    ADVISOR = "士"   # 士
    ELEPHANT = "象"  # 象
    HORSE = "马"     # 马
    ROOK = "车"      # 车
    CANNON = "炮"    # 炮
    PAWN = "兵"      # 兵/卒


class Piece:
    """棋子类"""
    
    # 棋子价值表（用于评估）
    PIECE_VALUES = {
        PieceType.KING: 10000,
        PieceType.ROOK: 90,
        PieceType.CANNON: 45,
        PieceType.HORSE: 40,
        PieceType.ELEPHANT: 20,
        PieceType.ADVISOR: 20,
        PieceType.PAWN: 10,
    }
    
    def __init__(self, piece_type: PieceType, is_red: bool, row: int, col: int):
        """
        初始化棋子
        
        Args:
            piece_type: 棋子类型
            is_red: 是否为红方（True=红方，False=黑方）
            row: 行坐标（0-9）
            col: 列坐标（0-8）
        """
        self.piece_type = piece_type
        self.is_red = is_red
        self.row = row
        self.col = col
    
    def get_value(self) -> int:
        """获取棋子价值"""
        return self.PIECE_VALUES[self.piece_type]
    
    def __repr__(self):
        color = "红" if self.is_red else "黑"
        return f"{color}{self.piece_type.value}({self.row},{self.col})"
    
    def copy(self):
        """复制棋子"""
        return Piece(self.piece_type, self.is_red, self.row, self.col)

