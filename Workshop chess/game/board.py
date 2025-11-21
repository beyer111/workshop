"""
中国象棋棋盘类
"""
from typing import List, Tuple, Optional
from .pieces import Piece, PieceType


class Board:
    """中国象棋棋盘（10行9列）"""
    
    ROWS = 10
    COLS = 9
    
    def __init__(self):
        """初始化棋盘"""
        self.grid: List[List[Optional[Piece]]] = [[None] * self.COLS for _ in range(self.ROWS)]
        self.move_history: List[Tuple[Tuple[int, int], Tuple[int, int], Optional[Piece]]] = []
        self._init_board()
    
    def _init_board(self):
        """初始化棋盘布局"""
        # 清空棋盘
        self.grid = [[None] * self.COLS for _ in range(self.ROWS)]
        
        # 红方（下方，行0-4）
        # 车
        self.grid[0][0] = Piece(PieceType.ROOK, True, 0, 0)
        self.grid[0][8] = Piece(PieceType.ROOK, True, 0, 8)
        # 马
        self.grid[0][1] = Piece(PieceType.HORSE, True, 0, 1)
        self.grid[0][7] = Piece(PieceType.HORSE, True, 0, 7)
        # 象
        self.grid[0][2] = Piece(PieceType.ELEPHANT, True, 0, 2)
        self.grid[0][6] = Piece(PieceType.ELEPHANT, True, 0, 6)
        # 士
        self.grid[0][3] = Piece(PieceType.ADVISOR, True, 0, 3)
        self.grid[0][5] = Piece(PieceType.ADVISOR, True, 0, 5)
        # 将
        self.grid[0][4] = Piece(PieceType.KING, True, 0, 4)
        # 炮
        self.grid[2][1] = Piece(PieceType.CANNON, True, 2, 1)
        self.grid[2][7] = Piece(PieceType.CANNON, True, 2, 7)
        # 兵
        for col in [0, 2, 4, 6, 8]:
            self.grid[3][col] = Piece(PieceType.PAWN, True, 3, col)
        
        # 黑方（上方，行5-9）
        # 车
        self.grid[9][0] = Piece(PieceType.ROOK, False, 9, 0)
        self.grid[9][8] = Piece(PieceType.ROOK, False, 9, 8)
        # 马
        self.grid[9][1] = Piece(PieceType.HORSE, False, 9, 1)
        self.grid[9][7] = Piece(PieceType.HORSE, False, 9, 7)
        # 象
        self.grid[9][2] = Piece(PieceType.ELEPHANT, False, 9, 2)
        self.grid[9][6] = Piece(PieceType.ELEPHANT, False, 9, 6)
        # 士
        self.grid[9][3] = Piece(PieceType.ADVISOR, False, 9, 3)
        self.grid[9][5] = Piece(PieceType.ADVISOR, False, 9, 5)
        # 将
        self.grid[9][4] = Piece(PieceType.KING, False, 9, 4)
        # 炮
        self.grid[7][1] = Piece(PieceType.CANNON, False, 7, 1)
        self.grid[7][7] = Piece(PieceType.CANNON, False, 7, 7)
        # 兵
        for col in [0, 2, 4, 6, 8]:
            self.grid[6][col] = Piece(PieceType.PAWN, False, 6, col)
    
    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        """获取指定位置的棋子"""
        if 0 <= row < self.ROWS and 0 <= col < self.COLS:
            return self.grid[row][col]
        return None
    
    def set_piece(self, row: int, col: int, piece: Optional[Piece]):
        """设置指定位置的棋子"""
        if 0 <= row < self.ROWS and 0 <= col < self.COLS:
            self.grid[row][col] = piece
            if piece:
                piece.row = row
                piece.col = col
    
    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        """
        移动棋子
        
        Args:
            from_pos: 起始位置 (row, col)
            to_pos: 目标位置 (row, col)
        
        Returns:
            是否移动成功
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        piece = self.get_piece(from_row, from_col)
        if piece is None:
            return False
        
        # 记录被吃的棋子
        captured = self.get_piece(to_row, to_col)
        
        # 移动棋子
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, None)
        
        # 记录历史
        self.move_history.append((from_pos, to_pos, captured))
        
        return True
    
    def undo_move(self) -> bool:
        """悔棋：撤销上一步"""
        if not self.move_history:
            return False
        
        from_pos, to_pos, captured = self.move_history.pop()
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # 恢复棋子位置
        piece = self.get_piece(to_row, to_col)
        if piece:
            self.set_piece(from_row, from_col, piece)
            self.set_piece(to_row, to_col, captured)
        
        return True
    
    def copy(self):
        """深拷贝棋盘"""
        new_board = Board()
        new_board.grid = [[None] * self.COLS for _ in range(self.ROWS)]
        for row in range(self.ROWS):
            for col in range(self.COLS):
                piece = self.grid[row][col]
                if piece:
                    new_board.grid[row][col] = piece.copy()
        new_board.move_history = self.move_history.copy()
        return new_board
    
    def is_in_palace(self, row: int, col: int, is_red: bool) -> bool:
        """判断位置是否在九宫格内"""
        if is_red:
            return 0 <= row <= 2 and 3 <= col <= 5
        else:
            return 7 <= row <= 9 and 3 <= col <= 5
    
    def is_over_river(self, row: int, is_red: bool) -> bool:
        """判断是否过河"""
        if is_red:
            return row >= 5  # 红方过河
        else:
            return row <= 4  # 黑方过河

    @property
    def pieces(self):
        """返回当前棋盘上的所有棋子列表"""
        all_pieces = []
        for row in range(self.ROWS):
            for col in range(self.COLS):
                piece = self.grid[row][col]
                if piece:
                    all_pieces.append(piece)
        return all_pieces

