"""
主窗口
"""
import tkinter as tk
from tkinter import messagebox
import threading
import time
import random
from typing import Optional, Tuple
from game.board import Board
from game.rules import Rules
from game.pieces import Piece, PieceType
from ai.beginner import BeginnerAI
from ai.intermediate import IntermediateAI
from ai.advanced import AdvancedAI
from utils.evaluator import Evaluator
from .board_widget import BoardWidget
from .control_panel import ControlPanel
from .evaluation_chart import EvaluationChart


class MainWindow:
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        self.root = tk.Tk()
        self.root.title("iChess Master: 多层次AI智能象棋系统")
        self.root.geometry("1000x700")
        
        self.board = Board()
        self.current_player_is_red = True  # 红方先行
        self.move_count = 0
        self.game_over = False
        self.game_started = False
        self.speed_mode = False
        self.speed_time_limit = 0.5
        self.acceleration_threshold = 100
        self.acceleration_mode = False
        self.intermediate_depth = 3
        self.intermediate_time_limit = 1.5
        self.intermediate_max_depth = 5
        
        # AI实例
        self.red_ai: Optional[object] = None
        self.black_ai: Optional[object] = None
        
        # 创建GUI组件
        self._create_widgets()
        
        # 更新显示
        self._update_display()
    
    def _create_widgets(self):
        """创建GUI组件"""
        # 主容器
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：棋盘
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, padx=5)
        
        self.board_widget = BoardWidget(left_frame)
        self.board_widget.pack()
        self.board_widget.set_board(self.board)
        self.board_widget.set_on_move(self._on_human_move)
        
        # 右侧：控制面板和图表
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # 控制面板
        self.control_panel = ControlPanel(right_frame)
        self.control_panel.pack(fill=tk.X, pady=5)
        self.control_panel.on_mode_change = self._on_mode_change
        self.control_panel.on_difficulty_change = self._on_difficulty_change
        self.control_panel.on_start_game = self._on_start_game
        self.control_panel.on_new_game = self._on_new_game
        self.control_panel.on_undo = self._on_undo
        self.control_panel.on_exit = self._on_exit
        self.control_panel.on_speed_mode_change = self._on_speed_mode_change
        
        # 评估曲线图
        chart_frame = tk.LabelFrame(right_frame, text="局势评估曲线", padx=10, pady=5)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        chart_frame.configure(height=220)
        chart_frame.pack_propagate(False)
        
        self.evaluation_chart = EvaluationChart(chart_frame, width=300, height=200)
        chart_scroll = tk.Scrollbar(chart_frame, orient=tk.VERTICAL, command=self.evaluation_chart.yview)
        self.evaluation_chart.configure(yscrollcommand=chart_scroll.set)
        
        self.evaluation_chart.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chart_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _on_human_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        """处理人类玩家走子"""
        if self.game_over:
            return

        if not self.game_started:
            self.control_panel.update_info("请先点击“开始游戏”按钮。")
            return
        
        # 检查当前玩家类型
        if self.current_player_is_red:
            player_type = self.control_panel.get_red_player()
        else:
            player_type = self.control_panel.get_black_player()
        
        if player_type != "human":
            return  # 当前不是人类玩家回合
        
        piece = self.board.get_piece(*from_pos)
        if not piece or piece.is_red != self.current_player_is_red:
            return
        
        # 执行走子
        if self.board.move_piece(from_pos, to_pos):
            self.move_count += 1
            self._check_acceleration_trigger()
            self._update_display()
            self._check_game_over()
            
            # 更新评估曲线
            if self.control_panel.get_mode() == "ai_vs_ai":
                red_score = Evaluator.evaluate(self.board, True)
                black_score = Evaluator.evaluate(self.board, False)
                self.evaluation_chart.add_score(red_score, black_score)
            
            # 切换玩家
            self.current_player_is_red = not self.current_player_is_red
            
            # 如果下一手是AI，自动走子
            self._check_ai_move()
    
    def _check_ai_move(self):
        """检查是否需要AI走子"""
        if self.game_over or not self.game_started:
            return
        
        # 确定当前玩家类型
        if self.current_player_is_red:
            player_type = self.control_panel.get_red_player()
        else:
            player_type = self.control_panel.get_black_player()
        
        if player_type != "human":
            # AI走子（在后台线程中执行）
            threading.Thread(target=self._ai_move, daemon=True).start()
    
    def _ai_move(self):
        """AI走子"""
        if self.game_over:
            return
        
        # 获取AI实例
        if self.current_player_is_red:
            ai = self._get_ai_instance(self.control_panel.get_red_player(), True)
        else:
            ai = self._get_ai_instance(self.control_panel.get_black_player(), False)
        
        if not ai:
            return
        
        # 记录开始时间
        start_time = time.time()
        
        # 获取AI走法
        move = ai.get_move(self.board, self.current_player_is_red)
        
        # 计算思考时间
        think_time = time.time() - start_time
        
        if move:
            if not (isinstance(move, (tuple, list)) and len(move) == 2 and
                    all(isinstance(pos, (tuple, list)) and len(pos) == 2 for pos in move)):
                self.control_panel.update_info("AI返回了非法走法，忽略本次操作。")
                return
            from_pos = (int(move[0][0]), int(move[0][1]))
            to_pos = (int(move[1][0]), int(move[1][1]))
            # 在主线程中执行走子
            self.root.after(0, self._execute_ai_move, from_pos, to_pos, think_time)
        else:
            # 无合法走法或AI未返回结果，检查是否结束
            self.control_panel.update_info("AI无合法走法，检测是否结束。")
            self.root.after(0, self._handle_no_move)

    def _handle_no_move(self):
        """AI无合法走法时的处理"""
        prev_game_over = self.game_over
        self._check_game_over()
        if not self.game_over and not prev_game_over:
            self.control_panel.update_info("未检测到将死/困毙，可能出现无可用走法的平局。")
    
    def _execute_ai_move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], think_time: float):
        """执行AI走子（在主线程中）"""
        if self.board.move_piece(from_pos, to_pos):
            self.move_count += 1
            self._check_acceleration_trigger()
            self._update_display()
            
            # 更新信息
            player_name = "红方" if self.current_player_is_red else "黑方"
            self.control_panel.update_info(
                f"{player_name} AI走子: ({from_pos[0]},{from_pos[1]}) -> ({to_pos[0]},{to_pos[1]})"
            )
            self.control_panel.update_info(f"AI思考时间: {think_time:.2f}秒")
            
            # 更新评估曲线
            if self.control_panel.get_mode() == "ai_vs_ai":
                red_score = Evaluator.evaluate(self.board, True)
                black_score = Evaluator.evaluate(self.board, False)
                self.evaluation_chart.add_score(red_score, black_score)
            
            self._check_game_over()
            
            # 切换玩家
            self.current_player_is_red = not self.current_player_is_red
            
            # 如果下一手还是AI，继续走子
            self._check_ai_move()
    
    def _get_ai_instance(self, player_type: str, is_red: bool):
        """获取AI实例"""
        if self.speed_mode and player_type != "human":
            return AdvancedAI(time_limit=self.speed_time_limit)
        
        if player_type == "beginner":
            return BeginnerAI()
        elif player_type == "intermediate":
            depth = self.intermediate_depth
            time_limit = self.intermediate_time_limit
            boost_applied = False
            
            if self.acceleration_mode:
                if random.choice([True, False]):
                    depth = min(depth + 1, self.intermediate_max_depth)
                    boost_applied = True
                steps_over = max(0, self.move_count - self.acceleration_threshold)
                decay_factor = 0.9 ** min(steps_over, 10)
                time_limit = max(0.2, time_limit * decay_factor)
                
                self.control_panel.update_info(
                    f"优化加速：{'增加深度' if boost_applied else '深度不变'}，"
                    f"深度={depth}，时间限制≈{time_limit:.2f}s"
                )
            
            return IntermediateAI(depth=depth, time_limit=time_limit)
        elif player_type == "advanced":
            return AdvancedAI()
        return None
    
    def _on_mode_change(self, mode: str):
        """模式改变"""
        mode_text = "AI观摩（AI对战）" if mode == "ai_vs_ai" else "人机对战"
        self.control_panel.update_info(f"模式已切换为：{mode_text}")
        self.control_panel.update_info("请点击“开始游戏”按钮以启动新对局。")
        # 切换模式后需要重新开始
        self.game_started = False
    
    def _on_speed_mode_change(self, enabled: bool):
        """加速模式切换"""
        self.speed_mode = enabled
        status = "开启" if enabled else "关闭"
        self.control_panel.update_info(f"加速模式已{status}。")
        if enabled:
            self.control_panel.update_info("AI将改用快速迭代加深（AdvancedAI），每步约0.5秒。")
        else:
            self.control_panel.update_info("AI恢复为各自选定的难度。")
    
    def _check_acceleration_trigger(self):
        """自动检测是否进入优化加速模式"""
        if not self.acceleration_mode and self.move_count >= self.acceleration_threshold:
            self.acceleration_mode = True
            self.control_panel.update_info(
                f"步数超过{self.acceleration_threshold}，进入优化加速模式（动态调整中级AI深度/时间）。"
            )
    
    def _on_difficulty_change(self, red_player: str, black_player: str):
        """难度改变"""
        # 如果当前是AI回合，可能需要重新获取AI实例
        pass
    
    def _reset_game_state(self):
        """重置游戏状态"""
        self.board = Board()
        self.current_player_is_red = True
        self.move_count = 0
        self.game_over = False
        self.game_started = False
        self.acceleration_mode = False
        self.evaluation_chart.clear()
        self.control_panel.clear_info()
        self._update_display()
        self.control_panel.update_info("新对局已准备好，点击“开始游戏”启动。")

    def _on_start_game(self):
        """开始游戏"""
        if self.game_over:
            messagebox.showinfo("提示", "当前对局已经结束，请先点击“新游戏”来重新开始。")
            return

        if self.game_started:
            messagebox.showinfo("提示", "对局已经在进行中。")
            return

        confirm = messagebox.askyesno("开始游戏", "确定要开始当前对局吗？")
        if not confirm:
            return

        self.game_started = True
        self.control_panel.update_info("对局开始！")
        self._check_ai_move()

    def _on_new_game(self):
        """新游戏"""
        confirm = messagebox.askyesno("新游戏", "确定要重新开始并清空当前对局吗？")
        if not confirm:
            return

        self._reset_game_state()
    
    def _on_undo(self):
        """悔棋"""
        if self.board.undo_move():
            self.move_count = max(0, self.move_count - 1)
            self.current_player_is_red = not self.current_player_is_red
            self._update_display()
            self.control_panel.update_info("已悔棋一步")
        else:
            self.control_panel.update_info("无法悔棋")
    
    def _on_exit(self):
        """退出游戏"""
        if messagebox.askokcancel("退出", "确定要退出游戏吗？"):
            self.root.quit()
    
    def _update_display(self):
        """更新显示"""
        self.board_widget.set_board(self.board)
        
        # 更新上一步走子标记
        if self.board.move_history:
            from_pos, to_pos, _ = self.board.move_history[-1]
            self.board_widget.set_last_move(from_pos, to_pos)
        else:
            self.board_widget.set_last_move(None, None)
        
        # 更新信息
        player_name = "红方" if self.current_player_is_red else "黑方"
        self.control_panel.update_info(f"当前回合: {player_name}")
        self.control_panel.update_info(f"总步数: {self.move_count}")
    
    def _check_game_over(self):
        """检查游戏是否结束"""
        # 检查是否被将死
        if Rules.is_checkmate(self.board, self.current_player_is_red):
            winner = "黑方" if self.current_player_is_red else "红方"
            loser = "红方" if self.current_player_is_red else "黑方"
            self.control_panel.update_info(f"{winner}获胜！{loser}被将死！")
            self.game_over = True
            self.game_started = False
            self.acceleration_mode = False
            
            # 显示更详细的弹窗
            message = f"🎉 游戏结束！\n\n{winner} 获胜！\n{loser} 被将死！\n\n总步数: {self.move_count}"
            messagebox.showinfo("游戏结束", message)
            return
        
        # 检查是否无子可动（困毙）
        # 如果is_checkmate返回False，但get_all_legal_moves返回空，说明是困毙
        all_moves = Rules.get_all_legal_moves(self.board, self.current_player_is_red)
        if not all_moves:
            # 如果is_checkmate返回False，说明没有被将军，那就是困毙
            # （将死的情况已经在上面处理了）
            if not Rules.is_checkmate(self.board, self.current_player_is_red):
                winner = "黑方" if self.current_player_is_red else "红方"
                loser = "红方" if self.current_player_is_red else "黑方"
                self.control_panel.update_info(f"{winner}获胜！{loser}无子可动（困毙）！")
                self.game_over = True
                self.game_started = False
                self.acceleration_mode = False
                
                # 显示弹窗
                message = f"🎉 游戏结束！\n\n{winner} 获胜！\n{loser} 无子可动（困毙）！\n\n总步数: {self.move_count}"
                messagebox.showinfo("游戏结束", message)
                return
    
    def run(self):
        """运行主循环"""
        # 如果初始是AI模式，自动开始
        self._check_ai_move()
        self.root.mainloop()

