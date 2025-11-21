"""
中国象棋走子规则
"""
from typing import List, Tuple
from .board import Board
from .pieces import Piece, PieceType


class Rules:
    """走子规则类"""
    
    @staticmethod
    def get_legal_moves(board: Board, piece: Piece) -> List[Tuple[int, int]]:
        """
        获取指定棋子的所有合法走法
        
        Args:
            board: 棋盘
            piece: 棋子
        
        Returns:
            合法走法列表 [(row, col), ...]
        """
        moves = Rules._get_moves_raw(board, piece)
        
        # 过滤掉会送将的走法
        legal_moves = []
        for move in moves:
            if Rules._is_legal_move(board, piece, move):
                legal_moves.append(move)
        
        return legal_moves
    
    @staticmethod
    def _get_moves_raw(board: Board, piece: Piece) -> List[Tuple[int, int]]:
        """不考虑送将，仅按棋子规则生成走法"""
        if piece.piece_type == PieceType.KING:
            return Rules._get_king_moves(board, piece)
        if piece.piece_type == PieceType.ADVISOR:
            return Rules._get_advisor_moves(board, piece)
        if piece.piece_type == PieceType.ELEPHANT:
            return Rules._get_elephant_moves(board, piece)
        if piece.piece_type == PieceType.HORSE:
            return Rules._get_horse_moves(board, piece)
        if piece.piece_type == PieceType.ROOK:
            return Rules._get_rook_moves(board, piece)
        if piece.piece_type == PieceType.CANNON:
            return Rules._get_cannon_moves(board, piece)
        if piece.piece_type == PieceType.PAWN:
            return Rules._get_pawn_moves(board, piece)
        return []
    
    @staticmethod
    def _get_king_moves(board: Board, piece: Piece) -> List[Tuple[int, int]]:
        """将/帅的走法"""
        moves = []
        row, col = piece.row, piece.col
        is_red = piece.is_red
        
        # 九宫格内的移动（上下左右各一格）
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if board.is_in_palace(new_row, new_col, is_red):
                target = board.get_piece(new_row, new_col)
                if target is None or target.is_red != is_red:
                    moves.append((new_row, new_col))
        
        # 将帅对脸（简化处理：允许直接吃对方将）
        if is_red:
            for r in range(row + 1, 10):
                target = board.get_piece(r, col)
                if target:
                    if target.piece_type == PieceType.KING and not target.is_red:
                        moves.append((r, col))
                    break
        else:
            for r in range(row - 1, -1, -1):
                target = board.get_piece(r, col)
                if target:
                    if target.piece_type == PieceType.KING and target.is_red:
                        moves.append((r, col))
                    break
        
        return moves
    
    @staticmethod
    def _get_advisor_moves(board: Board, piece: Piece) -> List[Tuple[int, int]]:
        """士的走法（斜线一格，只能在九宫格内）"""
        moves = []
        row, col = piece.row, piece.col
        is_red = piece.is_red
        
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if board.is_in_palace(new_row, new_col, is_red):
                target = board.get_piece(new_row, new_col)
                if target is None or target.is_red != is_red:
                    moves.append((new_row, new_col))
        
        return moves
    
    @staticmethod
    def _get_elephant_moves(board: Board, piece: Piece) -> List[Tuple[int, int]]:
        """象的走法（田字，不能过河）"""
        moves = []
        row, col = piece.row, piece.col
        is_red = piece.is_red
        
        directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            # 象不能过河
            if is_red and new_row > 4:
                continue
            if not is_red and new_row < 5:
                continue
            
            if 0 <= new_row < Board.ROWS and 0 <= new_col < Board.COLS:
                # 检查塞象眼
                block_row, block_col = row + dr // 2, col + dc // 2
                if board.get_piece(block_row, block_col) is None:
                    target = board.get_piece(new_row, new_col)
                    if target is None or target.is_red != is_red:
                        moves.append((new_row, new_col))
        
        return moves
    
    @staticmethod
    def _get_horse_moves(board: Board, piece: Piece) -> List[Tuple[int, int]]:
        """马的走法（日字，蹩马腿）"""
        moves = []
        row, col = piece.row, piece.col
        is_red = piece.is_red
        
        # 马的8个方向
        offsets = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for dr, dc in offsets:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < Board.ROWS and 0 <= new_col < Board.COLS:
                # 检查蹩马腿
                if abs(dr) == 2:
                    block_row, block_col = row + dr // 2, col
                else:
                    block_row, block_col = row, col + dc // 2
                
                if board.get_piece(block_row, block_col) is None:
                    target = board.get_piece(new_row, new_col)
                    if target is None or target.is_red != is_red:
                        moves.append((new_row, new_col))
        
        return moves
    
    @staticmethod
    def _get_rook_moves(board: Board, piece: Piece) -> List[Tuple[int, int]]:
        """车的走法（直线，无阻挡）"""
        moves = []
        row, col = piece.row, piece.col
        is_red = piece.is_red
        
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            for step in range(1, max(Board.ROWS, Board.COLS)):
                new_row, new_col = row + dr * step, col + dc * step
                if not (0 <= new_row < Board.ROWS and 0 <= new_col < Board.COLS):
                    break
                
                target = board.get_piece(new_row, new_col)
                if target is None:
                    moves.append((new_row, new_col))
                elif target.is_red != is_red:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
        
        return moves
    
    @staticmethod
    def _get_cannon_moves(board: Board, piece: Piece) -> List[Tuple[int, int]]:
        """炮的走法（直线，吃子需隔山打牛）"""
        moves = []
        row, col = piece.row, piece.col
        is_red = piece.is_red
        
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            found_piece = False
            for step in range(1, max(Board.ROWS, Board.COLS)):
                new_row, new_col = row + dr * step, col + dc * step
                if not (0 <= new_row < Board.ROWS and 0 <= new_col < Board.COLS):
                    break
                
                target = board.get_piece(new_row, new_col)
                if not found_piece:
                    if target is None:
                        moves.append((new_row, new_col))
                    else:
                        found_piece = True
                else:
                    if target is None:
                        continue
                    elif target.is_red != is_red:
                        moves.append((new_row, new_col))
                        break
                    else:
                        break
        
        return moves
    
    @staticmethod
    def _get_pawn_moves(board: Board, piece: Piece) -> List[Tuple[int, int]]:
        """兵/卒的走法（过河前只能向前，过河后可以左右）"""
        moves = []
        row, col = piece.row, piece.col
        is_red = piece.is_red
        
        if not board.is_over_river(row, is_red):
            # 未过河，只能向前
            if is_red:
                new_row = row + 1
            else:
                new_row = row - 1
            
            if 0 <= new_row < Board.ROWS:
                target = board.get_piece(new_row, col)
                if target is None or target.is_red != is_red:
                    moves.append((new_row, col))
        else:
            # 已过河，可以向前或左右
            if is_red:
                directions = [(1, 0), (0, -1), (0, 1)]
            else:
                directions = [(-1, 0), (0, -1), (0, 1)]
            
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < Board.ROWS and 0 <= new_col < Board.COLS:
                    target = board.get_piece(new_row, new_col)
                    if target is None or target.is_red != is_red:
                        moves.append((new_row, new_col))
        
        return moves
    
    @staticmethod
    def _is_legal_move(board: Board, piece: Piece, move: Tuple[int, int]) -> bool:
        """检查走法是否合法（不会送将）"""
        # 模拟走子
        test_board = board.copy()
        from_pos = (piece.row, piece.col)
        to_pos = move
        
        captured = test_board.get_piece(*to_pos)
        test_board.move_piece(from_pos, to_pos)
        
        # 检查是否被将死
        is_check = Rules._is_in_check(test_board, piece.is_red)
        
        return not is_check
    
    @staticmethod
    def _is_in_check(board: Board, is_red: bool) -> bool:
        """检查是否被将军"""
        # 找到将/帅的位置
        king_pos = None
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece and piece.piece_type == PieceType.KING and piece.is_red == is_red:
                    king_pos = (row, col)
                    break
            if king_pos:
                break
        
        if king_pos is None:
            return False
        
        # 检查对方所有棋子是否能攻击到将/帅
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece and piece.is_red != is_red:
                    moves = Rules._get_moves_raw(board, piece)
                    if king_pos in moves:
                        return True
        
        return False
    
    @staticmethod
    def is_checkmate(board: Board, is_red: bool) -> bool:
        """检查是否被将死"""
        if not Rules._is_in_check(board, is_red):
            return False
        
        # 检查是否有合法走法
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece and piece.is_red == is_red:
                    moves = Rules.get_legal_moves(board, piece)
                    if moves:
                        return False
        
        return True
    
    @staticmethod
    def get_all_legal_moves(board: Board, is_red: bool) -> List[Tuple[Piece, Tuple[int, int]]]:
        """获取一方的所有合法走法"""
        all_moves = []
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece and piece.is_red == is_red:
                    moves = Rules.get_legal_moves(board, piece)
                    for move in moves:
                        all_moves.append((piece, move))
        return all_moves

