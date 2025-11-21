"""
高级AI：Negamax + PVS + Killer Moves + LMR + Null Move + 深度静态搜索
结合多种非传统优化技术，显著超越Intermediate级别
"""
import time
from typing import Tuple, Optional, Dict, List
from game.board import Board
from game.rules import Rules
from utils.evaluator import Evaluator
from game.pieces import PieceType


class AdvancedAI:
    """高级AI：使用多种高级搜索优化技术"""
    
    def __init__(self, time_limit: float = 5.0):
        """
        初始化高级AI
        
        Args:
            time_limit: 思考时间限制（秒）
        """
        self.time_limit = time_limit
        self.start_time = 0
        
        # 置换表：存储局面评估结果
        self.transposition_table: Dict[int, Tuple[int, float, Optional[Tuple]]] = {}
        
        # Killer Moves：记录在相同深度造成剪枝的走法
        self.killer_moves: Dict[int, List[Tuple]] = {}  # depth -> [move1, move2]
        
        # Counter Moves：记录对特定走法的最佳应对
        self.counter_moves: Dict[Tuple, Tuple] = {}
        
        # 历史启发表：记录走法的历史表现
        self.history_table: Dict[Tuple, int] = {}
        
        # 局面历史：跟踪重复局面
        self.position_history: Dict[int, int] = {}  # hash -> count
        self.recent_positions: List[int] = []  # 最近20个局面
        self.no_capture_counter = 0  # 无吃子步数
        
        # 静态搜索深度
        self.max_quiescence_depth = 5  # 比Intermediate更深
        
        # 最大搜索深度（动态调整）
        self.base_max_depth = 8
        self.max_depth = 8
    
    def get_move(self, board: Board, is_red: bool) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        获取最佳走法（使用Negamax + PVS + 多种优化 + 智能时间管理）
        """
        # 1. 智能时间管理
        adaptive_time = self._adaptive_time_management(board, is_red)
        original_time_limit = self.time_limit
        self.time_limit = adaptive_time
        
        # 2. 关键局面识别
        position_type = self._identify_critical_position(board, is_red)
        
        # 3. 关键局面特殊处理
        critical_move = self._critical_position_strategy(board, is_red, position_type)
        if critical_move:
            self.time_limit = original_time_limit
            return critical_move
        
        # 4. 动态深度调整
        available_time = adaptive_time * 0.8  # 留20%余量
        adaptive_depth = self._get_adaptive_depth(available_time)
        self.max_depth = adaptive_depth
        
        self.start_time = time.time()
        all_moves = Rules.get_all_legal_moves(board, is_red)
        if not all_moves:
            self.time_limit = original_time_limit
            return None
        
        # 更新局面历史
        board_hash = self._zobrist_hash(board, is_red)
        self.position_history[board_hash] = self.position_history.get(board_hash, 0) + 1
        self.recent_positions.append(board_hash)
        if len(self.recent_positions) > 20:
            self.recent_positions.pop(0)
        
        # 检测重复局面
        repetition_count = self.position_history.get(board_hash, 0)
        is_repetition = repetition_count > 1
        
        # 清空killer moves（新一局）
        self.killer_moves.clear()
        
        # 如果检测到重复或无吃子步数过多，强制过滤重复走法
        if is_repetition or self.no_capture_counter > 5:
            non_repeating = self._filter_repeating_moves(board, all_moves, is_red)
            if non_repeating:
                all_moves = non_repeating
                # 如果过滤后没有走法，至少保留一个
                if not all_moves:
                    all_moves = Rules.get_all_legal_moves(board, is_red)
        
        # 使用高级走法排序
        sorted_moves = self._advanced_move_ordering(board, all_moves, is_red, 0, is_repetition)
        
        best_move = None
        best_score = float('-inf')
        
        # 迭代加深
        for depth in range(1, self.max_depth + 1):
            if time.time() - self.start_time >= self.time_limit * 0.9:
                break
                
            current_best = None
            current_score = float('-inf')
            
            # 重新排序（考虑新的killer moves）
            if depth > 1:
                sorted_moves = self._advanced_move_ordering(board, all_moves, is_red, depth, is_repetition)
            
            # 使用Principal Variation Search
            for idx, (piece, move) in enumerate(sorted_moves):
                if time.time() - self.start_time >= self.time_limit:
                    break
                
                test_board = board.copy()
                from_pos = (piece.row, piece.col)
                test_board.move_piece(from_pos, move)
                
                # 检查是否会导致重复局面（在搜索前给予惩罚）
                test_hash = self._zobrist_hash(test_board, not is_red)
                repeat_penalty = 0
                if test_hash in self.recent_positions[-3:]:
                    repeat_penalty = 2000  # 惩罚重复局面，但不直接丢弃走法
                
                # PVS: 第一个走法全窗口搜索，后续走法使用零窗口
                if idx == 0:
                    score = -self._negamax_pvs(test_board, depth - 1, not is_red, 
                                             float('-inf'), float('inf'), not is_red)
                else:
                    # Zero window search (null window)
                    score = -self._negamax_pvs(test_board, depth - 1, not is_red,
                                             -current_score - 1, -current_score, not is_red)
                    # 如果零窗口搜索失败，需要重新搜索
                    if current_score < score < float('inf'):
                        score = -self._negamax_pvs(test_board, depth - 1, not is_red,
                                                  float('-inf'), -current_score, not is_red)
                
                score -= repeat_penalty
                
                if score > current_score:
                    current_score = score
                    current_best = (from_pos, move)
                    
                    # 更新counter move
                    if len(self.counter_moves) < 1000:  # 限制大小
                        prev_move = self._get_last_move(board)
                        if prev_move:
                            self.counter_moves[prev_move] = (from_pos, move)
            
            if current_best:
                best_move = current_best
                best_score = current_score
                
                # 更新历史表
                self.history_table[best_move] = self.history_table.get(best_move, 0) + depth * depth
            
            # 如果找到必胜/必败，提前退出
            if abs(best_score) > 10000:
                break
        
        # 记录移动并检查吃子
        if best_move:
            target = board.get_piece(*best_move[1])
            if target:
                self.no_capture_counter = 0
            else:
                self.no_capture_counter += 1
        
        # 恢复原始时间限制
        self.time_limit = original_time_limit
        self.max_depth = self.base_max_depth
        
        return best_move
    
    def _negamax_pvs(self, board: Board, depth: int, is_red: bool, 
                 alpha: float, beta: float, maximizing_player: bool) -> float:
        """
        Negamax算法 + Principal Variation Search (PVS)
        PVS: 第一个走法全窗口搜索，后续走法使用零窗口（更高效）
        """
        # 时间检查
        if time.time() - self.start_time >= self.time_limit:
            return self._evaluate(board, maximizing_player)
        
        # 置换表查找
        board_hash = self._zobrist_hash(board, is_red)
        if board_hash in self.transposition_table:
            stored_depth, stored_score, stored_move = self.transposition_table[board_hash]
            if stored_depth >= depth:
                return stored_score
        
        # 检查将死
        if Rules.is_checkmate(board, is_red):
            return -100000 + (self.max_depth - depth) if is_red == maximizing_player else 100000 - (self.max_depth - depth)
        
        # Null Move Pruning（快速评估）
        if depth >= 3 and not Rules._is_in_check(board, is_red):
            null_score = -self._negamax_pvs(board, depth - 1 - 2, not is_red, 
                                          -beta, -beta + 1, not maximizing_player)
            if null_score >= beta:
                return beta
        
        # 终止条件：进入静态搜索
        if depth <= 0:
            return self._quiescence_search(board, is_red, alpha, beta, maximizing_player, self.max_quiescence_depth)
        
        all_moves = Rules.get_all_legal_moves(board, is_red)
        if not all_moves:
            return self._evaluate(board, maximizing_player)
        
        # 高级走法排序
        sorted_moves = self._advanced_move_ordering(board, all_moves, is_red, depth)
        
        best_score = float('-inf')
        best_move = None
        
        for idx, (piece, move) in enumerate(sorted_moves):
            if time.time() - self.start_time >= self.time_limit:
                break

            test_board = board.copy()
            from_pos = (piece.row, piece.col)
            test_board.move_piece(from_pos, move)

            # Late Move Reduction (LMR): 对后面的走法减少搜索深度
            reduction = 0
            if depth >= 3 and idx > 3 and not board.get_piece(*move):  # 非吃子走法
                reduction = 1 if idx > 6 else 0

            # PVS: 第一个走法全窗口，后续走法零窗口
            if idx == 0:
                score = -self._negamax_pvs(
                    test_board, depth - 1 - reduction, not is_red, -beta, -alpha, not maximizing_player
                )
            else:
                # Zero window search
                score = -self._negamax_pvs(
                    test_board, depth - 1 - reduction, not is_red, -alpha - 1, -alpha, not maximizing_player
                )
                # 如果零窗口失败，重新全窗口搜索
                if alpha < score < beta:
                    score = -self._negamax_pvs(
                        test_board, depth - 1 - reduction, not is_red, -beta, -score, not maximizing_player
                    )

            if score > best_score:
                best_score = score
                best_move = (from_pos, move)

            alpha = max(alpha, score)

            # Beta剪枝
            if alpha >= beta:
                # 更新killer move
                if depth not in self.killer_moves:
                    self.killer_moves[depth] = []
                if (from_pos, move) not in self.killer_moves[depth]:
                    self.killer_moves[depth].insert(0, (from_pos, move))
                    if len(self.killer_moves[depth]) > 2:
                        self.killer_moves[depth].pop()

                # 更新历史表
                self.history_table[(from_pos, move)] = self.history_table.get((from_pos, move), 0) + depth * depth
                break
        
        # 存储到置换表
        if len(self.transposition_table) < 10000:  # 限制大小
            self.transposition_table[board_hash] = (depth, best_score, best_move)
        
        return best_score
    
    def _quiescence_search(self, board: Board, is_red: bool, alpha: float, beta: float,
                          maximizing_player: bool, depth: int) -> float:
        """
        静态搜索：延伸吃子和威胁，避免地平线效应
        """
        # 基础评估
        stand_pat = self._evaluate(board, maximizing_player)
        
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat
        
        if depth <= 0 or time.time() - self.start_time >= self.time_limit:
            return stand_pat
        
        # 只搜索吃子和威胁走法
        capture_moves = self._get_capture_moves(board, is_red)
        threat_moves = self._get_threat_moves(board, is_red)
        all_important = capture_moves + threat_moves
        
        if not all_important:
            return stand_pat
        
        # 按MVV-LVA排序
        sorted_moves = self._mvv_lva_ordering(board, all_important, is_red)
        
        for piece, move in sorted_moves:
            if time.time() - self.start_time >= self.time_limit:
                break
            
            test_board = board.copy()
            from_pos = (piece.row, piece.col)
            test_board.move_piece(from_pos, move)
            
            score = -self._quiescence_search(test_board, not is_red, -beta, -alpha,
                                           not maximizing_player, depth - 1)
            
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        
        return alpha
    
    def _advanced_move_ordering(self, board: Board, moves: List, is_red: bool, depth: int, is_repetition: bool = False) -> List:
        """
        高级走法排序：结合多种启发式
        1. PV move (Principal Variation)
        2. 置换表中的最佳走法
        3. Killer moves
        4. Counter moves
        5. MVV-LVA (吃子)
        6. 历史启发
        7. 静态评估
        """
        scored_moves = []
        board_hash = self._zobrist_hash(board, is_red)
        
        # 获取置换表中的最佳走法
        tt_move = None
        if board_hash in self.transposition_table:
            _, _, tt_move = self.transposition_table[board_hash]
        
        # 获取counter move
        counter_move = None
        prev_move = self._get_last_move(board)
        if prev_move and prev_move in self.counter_moves:
            counter_move = self.counter_moves[prev_move]
        
        for piece, move in moves:
            from_pos = (piece.row, piece.col)
            move_tuple = (from_pos, move)
            score = 0
            
            # 1. PV move / TT move (最高优先级)
            if tt_move and move_tuple == tt_move:
                score += 100000
            # 2. Killer moves
            elif depth in self.killer_moves and move_tuple in self.killer_moves[depth]:
                score += 50000
            # 3. Counter move
            elif counter_move and move_tuple == counter_move:
                score += 30000
            # 4. MVV-LVA (吃子)
            target = board.get_piece(*move)
            if target and target.is_red != is_red:
                score += target.get_value() * 1000 - piece.get_value()
            # 5. 历史启发
            score += self.history_table.get(move_tuple, 0)
            # 6. 静态评估（棋子位置价值）
            score += self._static_move_value(board, piece, move, is_red)
            
            # 7. 重复惩罚（惩罚但不直接放弃）
            test_board = board.copy()
            test_board.move_piece(from_pos, move)
            new_hash = self._zobrist_hash(test_board, not is_red)
            
            # 检查是否会导致重复局面
            if new_hash in self.recent_positions[-3:]:  # 在最近3个局面中
                score -= 8000  # 惩罚重复走法
            elif new_hash in self.position_history and self.position_history[new_hash] > 1:
                score -= 3000  # 惩罚已知重复局面
            
            # 8. 变化奖励（鼓励改变局面的走法）
            if self.no_capture_counter > 3:
                # 如果长时间无吃子，优先选择有变化的走法
                if new_hash not in self.recent_positions[-5:]:  # 不在最近5个局面中
                    score += 5000  # 大幅奖励变化
                # 吃子走法额外奖励
                target = board.get_piece(*move)
                if target:
                    score += 2000  # 鼓励吃子打破僵局
            
            scored_moves.append((score, (piece, move)))
        
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return [move for _, move in scored_moves]
    
    def _mvv_lva_ordering(self, board: Board, moves: List, is_red: bool) -> List:
        """MVV-LVA排序：Most Valuable Victim - Least Valuable Attacker"""
        scored = []
        for piece, move in moves:
            target = board.get_piece(*move)
            if target:
                score = target.get_value() * 100 - piece.get_value()
            else:
                score = 0
            scored.append((score, (piece, move)))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [move for _, move in scored]
    
    def _get_capture_moves(self, board: Board, is_red: bool) -> List:
        """获取所有吃子走法"""
        captures = []
        for piece, move in Rules.get_all_legal_moves(board, is_red):
            target = board.get_piece(*move)
            if target and target.is_red != is_red:
                captures.append((piece, move))
        return captures
    
    def _get_threat_moves(self, board: Board, is_red: bool) -> List:
        """获取威胁走法（能攻击重要棋子）"""
        threats = []
        enemy_king = self._find_king(board, not is_red)
        
        for piece, move in Rules.get_all_legal_moves(board, is_red):
            # 威胁将/帅
            if enemy_king and move == enemy_king:
                threats.append((piece, move))
            # 威胁重要棋子
            target = board.get_piece(*move)
            if target and target.is_red != is_red:
                if target.piece_type in [PieceType.ROOK, PieceType.CANNON, PieceType.HORSE]:
                    threats.append((piece, move))
        
        return threats
    
    def _static_move_value(self, board: Board, piece, move: Tuple, is_red: bool) -> int:
        """静态走法价值评估"""
        value = 0
        
        # 中心控制
        row, col = move
        if 3 <= row <= 6 and 3 <= col <= 5:
            value += 5
        
        # 靠近敌方将
        enemy_king = self._find_king(board, not is_red)
        if enemy_king:
            distance = abs(row - enemy_king[0]) + abs(col - enemy_king[1])
            value += (10 - distance) * 2
        
        # 棋子机动性
        test_board = board.copy()
        from_pos = (piece.row, piece.col)
        test_board.move_piece(from_pos, move)
        new_piece = test_board.get_piece(*move)
        if new_piece:
            new_moves = Rules.get_legal_moves(test_board, new_piece)
            value += len(new_moves)

        # 开局阶段避免炮/车直接深入敌阵
        if len(board.move_history) < 10:
            if piece.piece_type in [PieceType.CANNON, PieceType.ROOK]:
                if (is_red and row >= 8) or ((not is_red) and row <= 1):
                    value -= 30
        
        return value
    
    def _evaluate(self, board: Board, is_red: bool) -> float:
        """评估函数（使用进攻性评估 + 额外特征 + 重复惩罚）"""
        return self._aggressive_evaluation(board, is_red)
    
    def _aggressive_evaluation(self, board: Board, is_red: bool) -> float:
        """增强的进攻性评估"""
        base_score = Evaluator.evaluate(board, is_red, use_position=True)
        
        # 1. 物质优势奖励
        material_advantage = self._calculate_material_advantage(board, is_red)
        
        # 2. 进攻性奖励（强烈鼓励进攻）
        offensive_potential = self._calculate_offensive_potential(board, is_red)
        
        # 3. 王的安全威胁
        king_threat = self._assess_king_threat(board, is_red)
        
        # 4. 进展性奖励（避免僵局）
        progress_bonus = self._calculate_progress_bonus(board, is_red)
        
        # 5. 额外评估特征
        mobility = self._calculate_mobility(board, is_red)
        king_safety = self._king_safety_score(board, is_red)
        piece_coordination = self._piece_coordination(board, is_red)
        
        # 6. 重复局面极强烈惩罚
        board_hash = self._zobrist_hash(board, is_red)
        repetition_penalty = 0
        if board_hash in self.recent_positions[-3:]:  # 在最近3个局面中
            repetition_penalty = 5000  # 极强烈惩罚
        elif board_hash in self.position_history:
            count = self.position_history[board_hash]
            repetition_penalty = count * 500  # 每次重复惩罚500分
        
        # 7. 无吃子惩罚（鼓励主动）
        no_capture_penalty = 0
        if self.no_capture_counter > 5:
            no_capture_penalty = (self.no_capture_counter - 5) * 50  # 更早开始惩罚，力度更大
        
        # 组合评估（大幅提升进攻权重）
        # 8. 自身王暴露惩罚
        own_king_penalty = self._own_king_exposure_penalty(board, is_red)
        
        aggressive_score = (
            base_score +
            material_advantage * 2.0 +        # 更重视子力优势
            offensive_potential * 1.0 +       # 降低进攻权重
            king_threat * 1.5 +               # 降低威胁权重
            progress_bonus * 1.0 +
            mobility * 0.5 +
            king_safety * 2.5 +
            piece_coordination * 0.5 -
            repetition_penalty -
            no_capture_penalty -
            own_king_penalty
        )
        
        return aggressive_score

    def _own_king_exposure_penalty(self, board: Board, is_red: bool) -> float:
        """如果己方王缺乏保护，则给予惩罚"""
        king_pos = self._find_king(board, is_red)
        if not king_pos:
            return 500  # 极端情况：无王，直接高惩罚
        
        row, col = king_pos
        defenders = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < Board.ROWS and 0 <= c < Board.COLS:
                    piece = board.get_piece(r, c)
                    if piece and piece.is_red == is_red:
                        defenders += 1
        # 如果防守者少于2个，按缺少的数量惩罚
        missing = max(0, 2 - defenders)
        return missing * 300
    
    def _calculate_mobility(self, board: Board, is_red: bool) -> float:
        """计算机动性"""
        mobility = 0
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece and piece.is_red == is_red:
                    moves = Rules.get_legal_moves(board, piece)
                    mobility += len(moves)
                    # 车炮的机动性更重要
                    if piece.piece_type in [PieceType.ROOK, PieceType.CANNON]:
                        mobility += len(moves) * 0.5
        return mobility
    
    def _king_safety_score(self, board: Board, is_red: bool) -> float:
        """王安全评估"""
        king_pos = self._find_king(board, is_red)
        if not king_pos:
            return -1000
        
        safety = 0
        row, col = king_pos
        
        # 在九宫内更安全
        if board.is_in_palace(row, col, is_red):
            safety += 20
        
        # 周围友方棋子保护
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
        safety += defenders * 10
        
        # 检查是否被攻击
        if Rules._is_in_check(board, is_red):
            safety -= 50
        
        return safety
    
    def _piece_coordination(self, board: Board, is_red: bool) -> float:
        """棋子协同评估"""
        coordination = 0
        
        # 车炮配合
        rooks_cannons = []
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece and piece.is_red == is_red:
                    if piece.piece_type in [PieceType.ROOK, PieceType.CANNON]:
                        rooks_cannons.append((row, col))
        
        # 车炮在同一线路上
        for i, (r1, c1) in enumerate(rooks_cannons):
            for r2, c2 in rooks_cannons[i+1:]:
                if r1 == r2 or c1 == c2:
                    coordination += 5
        
        return coordination
    
    def _find_king(self, board: Board, is_red: bool) -> Optional[Tuple[int, int]]:
        """找到将/帅位置"""
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece and piece.is_red == is_red and piece.piece_type == PieceType.KING:
                    return (row, col)
        return None
    
    def _zobrist_hash(self, board: Board, is_red: bool) -> int:
        """Zobrist哈希：快速局面哈希"""
        # 简化版：基于棋盘布局和当前玩家
        hash_val = 0
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece:
                    # 简单的哈希组合
                    piece_hash = hash((piece.piece_type.value, piece.is_red, row, col))
                    hash_val ^= piece_hash
        hash_val ^= hash(is_red)
        return hash_val
    
    def _get_last_move(self, board: Board) -> Optional[Tuple]:
        """获取上一步走法（用于counter move）"""
        if board.move_history:
            from_pos, to_pos, _ = board.move_history[-1]
            return (from_pos, to_pos)
        return None
    
    def _filter_repeating_moves(self, board: Board, moves: List, is_red: bool) -> List:
        """过滤掉会导致重复局面的走法"""
        non_repeating = []
        for piece, move in moves:
            test_board = board.copy()
            from_pos = (piece.row, piece.col)
            test_board.move_piece(from_pos, move)
            new_hash = self._zobrist_hash(test_board, not is_red)
            
            # 严格过滤：如果新局面在最近5个局面中，或者出现超过1次，则过滤掉
            if new_hash not in self.recent_positions[-5:] and self.position_history.get(new_hash, 0) <= 1:
                non_repeating.append((piece, move))
        
        # 如果过滤后还有走法，返回过滤后的；否则返回原始走法（至少保留一个）
        return non_repeating if non_repeating else moves
    
    def _adaptive_time_management(self, board: Board, is_red: bool) -> float:
        """自适应时间管理"""
        # 根据局面复杂度调整时间
        complexity = self._assess_position_complexity(board)
        
        if complexity == "high":  # 复杂局面
            return min(self.time_limit, 4.0)  # 最多4秒
        elif complexity == "medium":  # 中等局面
            return min(self.time_limit, 2.5)
        else:  # 简单局面
            return min(self.time_limit, 1.5)
    
    def _assess_position_complexity(self, board: Board) -> str:
        """评估局面复杂度"""
        piece_count = self._count_pieces(board)
        mobility = self._calculate_total_mobility(board)
        
        if piece_count <= 10 or mobility <= 20:
            return "low"
        elif piece_count <= 15 or mobility <= 40:
            return "medium"
        else:
            return "high"

    def _count_pieces(self, board: Board) -> int:
        """统计棋盘上的棋子数量"""
        count = 0
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                if board.get_piece(row, col):
                    count += 1
        return count
    
    def _calculate_total_mobility(self, board: Board) -> int:
        """计算总机动性"""
        total = 0
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece:
                    moves = Rules.get_legal_moves(board, piece)
                    total += len(moves)
        return total
    
    def _get_adaptive_depth(self, available_time: float) -> int:
        """根据可用时间动态调整深度"""
        # 预估各深度所需时间
        depth_time_requirements = {
            1: 0.1, 2: 0.3, 3: 1.0, 4: 3.0, 
            5: 8.0, 6: 20.0, 7: 50.0, 8: 120.0
        }
        
        # 选择在可用时间内能完成的最大深度
        for depth in sorted(depth_time_requirements.keys(), reverse=True):
            if depth_time_requirements[depth] <= available_time * 0.8:  # 留20%余量
                return depth
        
        return 2  # 兜底深度
    
    def _identify_critical_position(self, board: Board, is_red: bool) -> str:
        """识别关键局面"""
        # 物质优势判断
        material_diff = self._calculate_material_difference(board, is_red)
        
        # 局面控制判断
        position_control = self._calculate_position_control(board, is_red)
        
        # 如果具有明显优势，标记为关键局面
        if material_diff > 15 or position_control > 20:
            return "winning_advantage"
        elif material_diff < -15:
            return "losing_disadvantage"
        else:
            return "balanced"
    
    def _critical_position_strategy(self, board: Board, is_red: bool, position_type: str) -> Optional[Tuple]:
        """关键局面策略"""
        if position_type == "winning_advantage":
            # 优势局面：强制进攻
            return self._force_winning_attack(board, is_red)
        elif position_type == "losing_disadvantage":
            # 劣势局面：寻求复杂化
            return self._complicate_position(board, is_red)
        else:
            # 平衡局面：正常搜索
            return None
    
    def _force_winning_attack(self, board: Board, is_red: bool) -> Optional[Tuple]:
        """强制获胜攻击"""
        moves = Rules.get_all_legal_moves(board, is_red)
        if not moves:
            return None
        
        # 优先考虑将死走法
        for piece, move in moves:
            test_board = board.copy()
            test_board.move_piece((piece.row, piece.col), move)
            if Rules.is_checkmate(test_board, not is_red):
                return ((piece.row, piece.col), move)
        
        # 其次考虑将军走法
        for piece, move in moves:
            test_board = board.copy()
            test_board.move_piece((piece.row, piece.col), move)
            if Rules._is_in_check(test_board, not is_red):
                return ((piece.row, piece.col), move)
        
        # 最后考虑最大威胁走法
        best_threat = None
        best_threat_score = -1
        
        for piece, move in moves:
            threat_score = self._evaluate_threat(board, piece, move, is_red)
            if threat_score > best_threat_score:
                best_threat_score = threat_score
                best_threat = ((piece.row, piece.col), move)
        
        return best_threat
    
    def _complicate_position(self, board: Board, is_red: bool) -> Optional[Tuple]:
        """复杂化局面（劣势时）"""
        moves = Rules.get_all_legal_moves(board, is_red)
        if not moves:
            return None
        
        # 优先选择吃子走法
        captures = self._get_capture_moves(board, is_red)
        if captures:
            # 选择最有价值的吃子
            best_capture = None
            best_value = -1
            for piece, move in captures:
                target = board.get_piece(*move)
                if target and target.get_value() > best_value:
                    best_value = target.get_value()
                    best_capture = ((piece.row, piece.col), move)
            if best_capture:
                return best_capture
        
        # 其次选择威胁走法
        threats = self._get_threat_moves(board, is_red)
        if threats:
            return ((threats[0][0].row, threats[0][0].col), threats[0][1])
        
        return None
    
    def _evaluate_threat(self, board: Board, piece, move: Tuple, is_red: bool) -> float:
        """评估走法的威胁程度"""
        threat_score = 0
        
        # 吃子威胁
        target = board.get_piece(*move)
        if target:
            threat_score += target.get_value() * 10
        
        # 对王的威胁
        enemy_king = self._find_king(board, not is_red)
        if enemy_king:
            distance = abs(move[0] - enemy_king[0]) + abs(move[1] - enemy_king[1])
            threat_score += (10 - distance) * 5
        
        # 控制重要格子的威胁
        if 3 <= move[0] <= 6 and 3 <= move[1] <= 5:
            threat_score += 10
        
        return threat_score
    
    def _calculate_material_advantage(self, board: Board, is_red: bool) -> float:
        """计算物质优势"""
        red_value = 0
        black_value = 0
        
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece:
                    value = piece.get_value()
                    if piece.is_red:
                        red_value += value
                    else:
                        black_value += value
        
        if is_red:
            return red_value - black_value
        else:
            return black_value - red_value
    
    def _calculate_position_control(self, board: Board, is_red: bool) -> float:
        """计算局面控制"""
        control = 0
        
        # 中心控制
        for row in range(3, 7):
            for col in range(3, 6):
                piece = board.get_piece(row, col)
                if piece and piece.is_red == is_red:
                    control += 2
        
        # 机动性优势
        my_mobility = self._calculate_mobility(board, is_red)
        enemy_mobility = self._calculate_mobility(board, not is_red)
        control += (my_mobility - enemy_mobility) * 0.1
        
        return control
    
    def _calculate_material_difference(self, board: Board, is_red: bool) -> float:
        """计算物质差异"""
        return self._calculate_material_advantage(board, is_red)
    
    def _calculate_offensive_potential(self, board: Board, is_red: bool) -> float:
        """计算进攻潜力"""
        offensive_score = 0
        
        # 靠近敌方王的棋子获得奖励
        enemy_king = self._find_king(board, not is_red)
        if enemy_king:
            for row in range(Board.ROWS):
                for col in range(Board.COLS):
                    piece = board.get_piece(row, col)
                    if piece and piece.is_red == is_red:
                        distance = abs(row - enemy_king[0]) + abs(col - enemy_king[1])
                        # 越靠近敌方王奖励越高
                        proximity_bonus = max(0, 20 - distance * 2)
                        offensive_score += proximity_bonus
                        
                        # 攻击性棋子额外奖励
                        if piece.piece_type in [PieceType.ROOK, PieceType.CANNON, PieceType.HORSE]:
                            offensive_score += 10
        
        return offensive_score
    
    def _assess_king_threat(self, board: Board, is_red: bool) -> float:
        """评估对敌方王的威胁"""
        threat_score = 0
        enemy_king = self._find_king(board, not is_red)
        
        if enemy_king:
            # 检查是否能直接攻击王
            for row in range(Board.ROWS):
                for col in range(Board.COLS):
                    piece = board.get_piece(row, col)
                    if piece and piece.is_red == is_red:
                        moves = Rules.get_legal_moves(board, piece)
                        if enemy_king in moves:
                            threat_score += 50  # 直接攻击王的巨大奖励
            
            # 检查是否控制王周围的格子
            control_bonus = self._calculate_king_control(board, is_red, enemy_king)
            threat_score += control_bonus
        
        return threat_score
    
    def _calculate_king_control(self, board: Board, is_red: bool, king_pos: Tuple[int, int]) -> float:
        """计算对王周围格子的控制"""
        control = 0
        row, col = king_pos
        
        # 检查王周围8个格子
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                r, c = row + dr, col + dc
                if 0 <= r < Board.ROWS and 0 <= c < Board.COLS:
                    # 检查是否能攻击这个格子
                    for piece_row in range(Board.ROWS):
                        for piece_col in range(Board.COLS):
                            piece = board.get_piece(piece_row, piece_col)
                            if piece and piece.is_red == is_red:
                                moves = Rules.get_legal_moves(board, piece)
                                if (r, c) in moves:
                                    control += 5
                                    break
        
        return control
    
    def _calculate_progress_bonus(self, board: Board, is_red: bool) -> float:
        """计算进展性奖励"""
        bonus = 0
        
        # 鼓励吃子
        # 这个在评估中已经考虑了
        
        # 鼓励推进棋子
        for row in range(Board.ROWS):
            for col in range(Board.COLS):
                piece = board.get_piece(row, col)
                if piece and piece.is_red == is_red:
                    if piece.piece_type == PieceType.PAWN:
                        target_row = 9 if is_red else 0
                        distance = abs(row - target_row)
                        bonus += (9 - distance) * 2
        
        return bonus
