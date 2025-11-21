"""
控制面板组件
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


class ControlPanel(tk.Frame):
    """控制面板"""
    
    def __init__(self, parent, *args, **kwargs):
        """初始化控制面板"""
        super().__init__(parent, *args, **kwargs)
        
        self.on_mode_change: Optional[Callable] = None
        self.on_difficulty_change: Optional[Callable] = None
        self.on_start_game: Optional[Callable] = None
        self.on_new_game: Optional[Callable] = None
        self.on_undo: Optional[Callable] = None
        self.on_exit: Optional[Callable] = None
        self.on_speed_mode_change: Optional[Callable[[bool], None]] = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 模式选择
        mode_frame = tk.LabelFrame(self, text="游戏模式", padx=10, pady=5)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mode_var = tk.StringVar(value="human_vs_ai")
        tk.Radiobutton(mode_frame, text="人机对战", variable=self.mode_var, 
                      value="human_vs_ai", command=self._on_mode_change).pack(anchor=tk.W)
        tk.Radiobutton(mode_frame, text="AI观摩", variable=self.mode_var, 
                      value="ai_vs_ai", command=self._on_mode_change).pack(anchor=tk.W)
        
        # 难度选择
        difficulty_frame = tk.LabelFrame(self, text="AI难度", padx=10, pady=5)
        difficulty_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 红方选择
        red_frame = tk.Frame(difficulty_frame)
        red_frame.pack(fill=tk.X, pady=2)
        tk.Label(red_frame, text="红方:").pack(side=tk.LEFT)
        self.red_var = tk.StringVar(value="human")
        red_combo = ttk.Combobox(red_frame, textvariable=self.red_var, 
                                values=["human", "beginner", "intermediate", "advanced"],
                                state="readonly", width=12)
        red_combo.pack(side=tk.LEFT, padx=5)
        red_combo.bind("<<ComboboxSelected>>", self._on_difficulty_change)
        
        # 黑方选择
        black_frame = tk.Frame(difficulty_frame)
        black_frame.pack(fill=tk.X, pady=2)
        tk.Label(black_frame, text="黑方:").pack(side=tk.LEFT)
        self.black_var = tk.StringVar(value="intermediate")
        black_combo = ttk.Combobox(black_frame, textvariable=self.black_var,
                                  values=["human", "beginner", "intermediate", "advanced"],
                                  state="readonly", width=12)
        black_combo.pack(side=tk.LEFT, padx=5)
        black_combo.bind("<<ComboboxSelected>>", self._on_difficulty_change)
        
        # 游戏控制按钮
        control_frame = tk.LabelFrame(self, text="游戏控制", padx=10, pady=5)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(control_frame, text="开始游戏", command=self._on_start_game,
                 width=15).pack(pady=2)
        tk.Button(control_frame, text="新游戏", command=self._on_new_game,
                 width=15).pack(pady=2)
        tk.Button(control_frame, text="悔棋", command=self._on_undo,
                 width=15).pack(pady=2)
        tk.Button(control_frame, text="退出", command=self._on_exit,
                 width=15).pack(pady=2)
        
        # 加速模式
        speed_frame = tk.LabelFrame(self, text="加速模式", padx=10, pady=5)
        speed_frame.pack(fill=tk.X, padx=5, pady=5)
        self.speed_mode_var = tk.BooleanVar(value=False)
        tk.Checkbutton(speed_frame, text="启用加速（AI使用快速模式）", 
                       variable=self.speed_mode_var, command=self._on_speed_mode_change).pack(anchor=tk.W)
        
        # 信息显示
        info_frame = tk.LabelFrame(self, text="游戏信息", padx=10, pady=5)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.info_text = tk.Text(info_frame, height=8, width=25, wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(info_frame, command=self.info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
    
    def _on_mode_change(self):
        """模式改变回调"""
        if self.on_mode_change:
            self.on_mode_change(self.mode_var.get())

    def _on_start_game(self):
        """开始游戏回调"""
        if self.on_start_game:
            self.on_start_game()

    def _on_new_game(self):
        """新游戏回调"""
        if self.on_new_game:
            self.on_new_game()

    def _on_undo(self):
        """悔棋回调"""
        if self.on_undo:
            self.on_undo()

    def _on_exit(self):
        """退出回调"""
        if self.on_exit:
            self.on_exit()

    def _on_speed_mode_change(self):
        """加速模式切换"""
        if self.on_speed_mode_change:
            self.on_speed_mode_change(self.speed_mode_var.get())
    
    def is_speed_mode(self) -> bool:
        """是否启用加速模式"""
        return self.speed_mode_var.get()
    
    def _on_difficulty_change(self, event=None):
        """难度改变回调"""
        if self.on_difficulty_change:
            self.on_difficulty_change(
                self.red_var.get(),
                self.black_var.get()
            )
    
    def update_info(self, text: str):
        """更新信息显示"""
        self.info_text.insert(tk.END, text + "\n")
        self.info_text.see(tk.END)
    
    def clear_info(self):
        """清空信息显示"""
        self.info_text.delete(1.0, tk.END)
    
    def get_mode(self) -> str:
        """获取当前模式"""
        return self.mode_var.get()
    
    def get_red_player(self) -> str:
        """获取红方玩家类型"""
        return self.red_var.get()
    
    def get_black_player(self) -> str:
        """获取黑方玩家类型"""
        return self.black_var.get()

