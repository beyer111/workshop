"""
初级AI：基于规则的贪婪算法
"""
import random
from typing import Tuple, Optional
from game.board import Board
from game.rules import Rules
from utils.evaluator import Evaluator


class BeginnerAI:
    """初级AI：贪婪算法 + 随机性"""
    
    def __init__(self, randomness: float = 0.2):
        """
        初始化初级AI
        
        Args:
            randomness: 随机选择走法的概率（0-1）
        """
        self.randomness = randomness
    
    def get_move(self, board: Board, is_red: bool) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        获取最佳走法
        
        Args:
            board: 当前棋盘
            is_red: AI是否为红方
        
        Returns:
            ((from_row, from_col), (to_row, to_col)) 或 None
        """
        all_moves = Rules.get_all_legal_moves(board, is_red)
        if not all_moves:
            return None
        
        # 评估所有走法
        scored_moves = []
        for piece, move in all_moves:
            # 模拟走子
            test_board = board.copy()
            from_pos = (piece.row, piece.col)
            test_board.move_piece(from_pos, move)
            
            # 评估局面
            score = Evaluator.evaluate(test_board, is_red, use_position=False)
            scored_moves.append((score, (from_pos, move)))
        
        # 按分数排序
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        
        # 以一定概率选择最佳走法，否则随机选择
        if random.random() > self.randomness and scored_moves:
            return scored_moves[0][1]
        elif all_moves:
            piece, move = random.choice(all_moves)
            from_pos = (piece.row, piece.col)
            return (from_pos, move)
        return None

