"""
棋盘组件
"""
import tkinter as tk
from typing import Optional, Callable, Tuple
from game.board import Board
from game.pieces import Piece


class BoardWidget(tk.Canvas):
    """棋盘画布组件"""
    
    ROWS = 10
    COLS = 9
    CELL_SIZE = 50
    BOARD_WIDTH = COLS * CELL_SIZE
    BOARD_HEIGHT = ROWS * CELL_SIZE
    
    def __init__(self, parent, *args, **kwargs):
        """初始化棋盘组件"""
        width = self.COLS * self.CELL_SIZE
        height = self.ROWS * self.CELL_SIZE
        super().__init__(parent, width=width, height=height, bg='#DEB887', *args, **kwargs)
        
        self.board: Optional[Board] = None
        self.selected_piece: Optional[Piece] = None
        self.legal_moves: list = []
        self.last_move: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
        self.on_move_callback: Optional[Callable] = None
        
        self.bind("<Button-1>", self._on_click)
        
        # 绘制棋盘网格
        self._draw_grid()
    
    def set_board(self, board: Board):
        """设置棋盘"""
        self.board = board
        self._redraw()
    
    def set_on_move(self, callback: Callable):
        """设置走子回调函数"""
        self.on_move_callback = callback
    
    def set_selected_piece(self, piece: Optional[Piece], legal_moves: list = None):
        """设置选中的棋子"""
        self.selected_piece = piece
        self.legal_moves = legal_moves or []
        self._redraw()
    
    def set_last_move(self, from_pos: Optional[Tuple[int, int]], 
                     to_pos: Optional[Tuple[int, int]]):
        """设置上一步走子"""
        if from_pos and to_pos:
            self.last_move = (from_pos, to_pos)
        else:
            self.last_move = None
        self._redraw()
    
    def _draw_grid(self):
        """绘制棋盘网格"""
        self.delete("grid")
        
        # 绘制横线
        for row in range(self.ROWS):
            y = row * self.CELL_SIZE
            self.create_line(0, y, self.COLS * self.CELL_SIZE, y, 
                           fill='black', width=1, tags="grid")
        
        # 绘制竖线
        for col in range(self.COLS):
            x = col * self.CELL_SIZE
            self.create_line(x, 0, x, self.ROWS * self.CELL_SIZE, 
                           fill='black', width=1, tags="grid")
        
        # 绘制楚河汉界
        river_y = 4.5 * self.CELL_SIZE
        self.create_line(0, river_y, self.COLS * self.CELL_SIZE, river_y, 
                        fill='black', width=2, tags="grid")
    
    def _redraw(self):
        """重绘棋盘"""
        self.delete("piece", "highlight", "legal_move", "last_move")
        
        if not self.board:
            return
        
        # 绘制上一步走子标记
        if self.last_move:
            from_pos, to_pos = self.last_move
            self._draw_cell_highlight(from_pos[0], from_pos[1], "yellow", "last_move")
            self._draw_cell_highlight(to_pos[0], to_pos[1], "yellow", "last_move")
        
        # 绘制选中棋子高亮
        if self.selected_piece:
            self._draw_cell_highlight(self.selected_piece.row, self.selected_piece.col, 
                                     "lightblue", "highlight")
        
        # 绘制合法走法提示
        for row, col in self.legal_moves:
            x = col * self.CELL_SIZE + self.CELL_SIZE // 2
            y = row * self.CELL_SIZE + self.CELL_SIZE // 2
            self.create_oval(x - 8, y - 8, x + 8, y + 8, 
                           fill='green', outline='darkgreen', width=2, 
                           tags="legal_move")
        
        # 绘制棋子
        for row in range(self.ROWS):
            for col in range(self.COLS):
                piece = self.board.get_piece(row, col)
                if piece:
                    self._draw_piece(piece)
    
    def _draw_cell_highlight(self, row: int, col: int, color: str, tag: str):
        """绘制单元格高亮"""
        x1 = col * self.CELL_SIZE
        y1 = row * self.CELL_SIZE
        x2 = x1 + self.CELL_SIZE
        y2 = y1 + self.CELL_SIZE
        self.create_rectangle(x1, y1, x2, y2, fill=color, 
                            outline='', tags=tag, stipple='gray50')
    
    def _draw_piece(self, piece: Piece):
        """绘制棋子"""
        row, col = piece.row, piece.col
        x = col * self.CELL_SIZE + self.CELL_SIZE // 2
        y = row * self.CELL_SIZE + self.CELL_SIZE // 2
        
        # 绘制棋子背景（圆形）
        bg_color = '#FF6B6B' if piece.is_red else '#4ECDC4'
        self.create_oval(x - 20, y - 20, x + 20, y + 20, 
                        fill=bg_color, outline='black', width=2, tags="piece")
        
        # 绘制棋子文字
        piece_name = piece.piece_type.value
        text_color = 'white' if piece.is_red else 'black'
        self.create_text(x, y, text=piece_name, fill=text_color, 
                        font=('Arial', 14, 'bold'), tags="piece")
    
    def _on_click(self, event):
        """处理鼠标点击"""
        if not self.board or not self.on_move_callback:
            return
        
        col = event.x // self.CELL_SIZE
        row = event.y // self.CELL_SIZE
        
        if not (0 <= row < self.ROWS and 0 <= col < self.COLS):
            return
        
        clicked_piece = self.board.get_piece(row, col)
        
        # 如果点击了合法走法位置
        if self.selected_piece and (row, col) in self.legal_moves:
            from_pos = (self.selected_piece.row, self.selected_piece.col)
            to_pos = (row, col)
            self.on_move_callback(from_pos, to_pos)
            self.set_selected_piece(None)
            return
        
        # 如果点击了棋子，选中它（由主窗口判断是否为当前玩家的棋子）
        if clicked_piece:
            from game.rules import Rules
            legal_moves = Rules.get_legal_moves(self.board, clicked_piece)
            self.set_selected_piece(clicked_piece, legal_moves)
        else:
            self.set_selected_piece(None)

