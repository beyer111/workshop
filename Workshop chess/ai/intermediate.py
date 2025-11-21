"""
中级AI：Minimax + Alpha-Beta + 轻量迭代加深
"""
import time
from typing import Tuple, Optional, List
from game.board import Board
from game.rules import Rules
from utils.evaluator import Evaluator
from game.pieces import PieceType


class IntermediateAI:
    """
    改进版中级AI：
    - 使用带时间限制的迭代加深（最大深度 <= depth）
    - 简单走法排序（吃子优先、逼近将优先）
    - 无历史表和复杂启发，计算量介于 beginner 与 advanced 之间
    """
    
    def __init__(self, depth: int = 4, time_limit: float = 1.8):
        self.max_depth = max(1, depth)
        self.time_limit = time_limit
        self._start_time = 0.0
        self._best_move: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    
    def get_move(self, board: Board, is_red: bool) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        all_moves = Rules.get_all_legal_moves(board, is_red)
        if not all_moves:
            return None
        
        self._start_time = time.time()
        ordered_moves = self._order_moves(board, all_moves, is_red)
        self._best_move = None
        
        for depth in range(1, self.max_depth + 1):
            if self._time_exceeded():
                break
            
            current_best = None
            current_score = float('-inf')
            
            for piece, move in ordered_moves:
                if self._time_exceeded():
                    break
                
                test_board = board.copy()
                from_pos = (piece.row, piece.col)
                test_board.move_piece(from_pos, move)
                
                score = self._minimax(test_board, depth - 1, not is_red, 
                                      float('-inf'), float('inf'), is_red)
                
                if score > current_score:
                    current_score = score
                    current_best = (from_pos, move)
            
            if current_best:
                self._best_move = current_best
                ordered_moves = self._promote_move(ordered_moves, current_best)
        
        if self._best_move:
            return self._best_move
        
        # 超时或异常时返回第一个合法走法
        piece, move = ordered_moves[0]
        return ((piece.row, piece.col), move)
    
    def _minimax(self, board: Board, depth: int, is_red: bool, 
                 alpha: float, beta: float, maximizing_player: bool) -> float:
        if self._time_exceeded():
            return Evaluator.evaluate(board, maximizing_player, use_position=True)
        
        if depth == 0:
            return Evaluator.evaluate(board, maximizing_player, use_position=True)
        
        if Rules.is_checkmate(board, is_red):
            if is_red == maximizing_player:
                return float('-inf')
            else:
                return float('inf')
        
        all_moves = Rules.get_all_legal_moves(board, is_red)
        if not all_moves:
            return Evaluator.evaluate(board, maximizing_player, use_position=True)
        
        ordered_moves = self._order_moves(board, all_moves, is_red)
        
        if is_red == maximizing_player:
            value = float('-inf')
            for piece, move in ordered_moves:
                if self._time_exceeded():
                    break
                
                test_board = board.copy()
                from_pos = (piece.row, piece.col)
                test_board.move_piece(from_pos, move)
                
                score = self._minimax(test_board, depth - 1, not is_red, 
                                     alpha, beta, maximizing_player)
                value = max(value, score)
                alpha = max(alpha, score)
                
                if beta <= alpha:
                    break
            
            return value
        else:
            value = float('inf')
            for piece, move in ordered_moves:
                if self._time_exceeded():
                    break
                
                test_board = board.copy()
                from_pos = (piece.row, piece.col)
                test_board.move_piece(from_pos, move)
                
                score = self._minimax(test_board, depth - 1, not is_red, 
                                     alpha, beta, maximizing_player)
                value = min(value, score)
                beta = min(beta, score)
                
                if beta <= alpha:
                    break
            
            return value
    
    def _order_moves(self, board: Board, moves: List[Tuple], is_red: bool) -> List[Tuple]:
        """
        简单走法排序：优先吃子和靠近敌方将的位置
        """
        scored_moves = []
        enemy_king_pos = self._find_king(board, not is_red)
        
        for piece, move in moves:
            target = board.get_piece(*move)
            capture_value = 0
            if target and target.is_red != piece.is_red:
                capture_value = target.get_value()
            
            king_distance = 0
            if enemy_king_pos:
                king_distance = abs(move[0] - enemy_king_pos[0]) + abs(move[1] - enemy_king_pos[1])
            
            score = capture_value - 0.1 * king_distance
            scored_moves.append((score, piece, move))
        
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return [(piece, move) for _, piece, move in scored_moves]
    
    def _promote_move(self, moves: List[Tuple], best_move: Tuple[Tuple[int, int], Tuple[int, int]]) -> List[Tuple]:
        """将上一轮搜索的最佳走法移到列表前面（PV move ordering）"""
        from_pos, to_pos = best_move
        for idx, (piece, move) in enumerate(moves):
            if (piece.row, piece.col) == from_pos and move == to_pos:
                moves.insert(0, moves.pop(idx))
                break
        return moves
    
    def _find_king(self, board: Board, is_red: bool):
        """找到指定阵营将的位置（用于简单排序）"""
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece and piece.is_red == is_red and piece.piece_type == PieceType.KING:
                    return (row, col)
        return None
    
    def _time_exceeded(self) -> bool:
        """检查是否超过时间限制"""
        if self.time_limit <= 0:
            return False
        return (time.time() - self._start_time) >= self.time_limit

