"""
评估曲线图组件
"""
import tkinter as tk
from typing import List


class EvaluationChart(tk.Canvas):
    """评估曲线图"""
    
    def __init__(self, parent, width=300, height=200, *args, **kwargs):
        """初始化图表"""
        super().__init__(parent, width=width, height=height, bg='white', *args, **kwargs)
        
        self.width = width
        self.height = height
        self.padding = 40
        
        self.red_scores: List[float] = []
        self.black_scores: List[float] = []
        self.max_score = 1000
        self.min_score = -1000
    
    def add_score(self, red_score: float, black_score: float):
        """添加评估分数"""
        self.red_scores.append(red_score)
        self.black_scores.append(black_score)
        self._redraw()
    
    def clear(self):
        """清空数据"""
        self.red_scores = []
        self.black_scores = []
        self._redraw()
    
    def _redraw(self):
        """重绘图表"""
        self.delete("all")
        
        # 计算坐标范围
        chart_width = self.width - 2 * self.padding
        chart_height = self.height - 2 * self.padding
        self._draw_axes(chart_height)
        
        if not self.red_scores:
            self.create_text(self.width // 2, self.height // 2, text="暂无数据", fill='gray')
            self.configure(scrollregion=(0, 0, self.width, self.height))
            return
        
        # 绘制曲线
        if len(self.red_scores) > 1:
            self._draw_curve(self.red_scores, '#FF6B6B', "红方")
        if len(self.black_scores) > 1:
            self._draw_curve(self.black_scores, '#4ECDC4', "黑方")
        
        self.configure(scrollregion=self.bbox("all"))
    
    def _draw_curve(self, scores: List[float], color: str, label: str):
        """绘制一条曲线"""
        chart_width = self.width - 2 * self.padding
        chart_height = self.height - 2 * self.padding
        
        # 归一化分数
        max_val = max(max(scores), abs(min(scores)), 1)
        normalized = [s / max_val for s in scores]
        
        points = []
        for i, score in enumerate(normalized):
            x = self.padding + (i / max(len(scores) - 1, 1)) * chart_width
            y = self.height - self.padding - (score + 1) * chart_height / 2
            points.append((x, y))
        
        # 绘制折线
        if len(points) > 1:
            for i in range(len(points) - 1):
                self.create_line(points[i][0], points[i][1], 
                                points[i+1][0], points[i+1][1], 
                                fill=color, width=2)
        
        # 绘制数据点
        for x, y in points:
            self.create_oval(x - 3, y - 3, x + 3, y + 3, 
                           fill=color, outline=color)
        
        # 绘制图例
        legend_y = 10 + (20 if "红" in label else 0)
        self.create_oval(10, legend_y - 5, 20, legend_y + 5, fill=color, outline=color)
        self.create_text(25, legend_y, text=label, anchor=tk.W, font=('Arial', 9))
    
    def _draw_axes(self, chart_height: int):
        """绘制坐标轴和零线"""
        # 绘制坐标轴
        self.create_line(self.padding, self.padding, 
                        self.padding, self.height - self.padding, 
                        fill='black', width=2)  # Y轴
        self.create_line(self.padding, self.height - self.padding, 
                        self.width - self.padding, self.height - self.padding, 
                        fill='black', width=2)  # X轴
        
        # 绘制零线
        zero_y = self.height - self.padding - chart_height // 2
        self.create_line(self.padding, zero_y, 
                        self.width - self.padding, zero_y, 
                        fill='gray', dash=(5, 5))
        
        # 绘制标签
        self.create_text(self.padding // 2, self.height // 2, 
                        text="评估", angle=90, font=('Arial', 10))
        self.create_text(self.width // 2, self.height - self.padding // 2, 
                        text="步数", font=('Arial', 10))

