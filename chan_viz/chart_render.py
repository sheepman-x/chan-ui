import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict

class PlotlyChartRenderer:
    """Plotly图表渲染器"""
    
    def __init__(self):
        self.colors = {
            'bi': '#FF6B6B',
            'zs': '#45B7D1', 
            'seg': '#4ECDC4',
            'bsp_buy': '#00FF00',
            'bsp_sell': '#FF0000'
        }
    
    def create_chan_chart(self, data: Dict, level: str, code: str = "") -> go.Figure:
        """创建缠论核心图表 - 只包含K线和缠论指标"""
        
        # 创建基础图形 - 单行显示，专注核心
        fig = go.Figure()
        
        # 添加K线图
        fig.add_trace(go.Candlestick(
            x=data['kline']['dates'],
            open=data['kline']['open'],
            high=data['kline']['high'],
            low=data['kline']['low'],
            close=data['kline']['close'],
            name='K线',
            increasing_line_color='red',  # A股红色上涨
            decreasing_line_color='green'
        ))
        
        # 添加笔 - 细线显示
        if 'bi' in data and data['bi']:
            for bi in data['bi']:
                fig.add_trace(go.Scatter(
                    x=bi['x'],
                    y=bi['y'],
                    mode='lines+markers',
                    name='笔',
                    line=dict(color=self.colors['bi'], width=1.5),
                    marker=dict(size=4),
                    hoverinfo='y+name'
                ))
        
        # 添加中枢 - 半透明矩形填充
        if 'central_zone' in data:
            for i, zs in enumerate(data['central_zone']):
                fig.add_trace(go.Scatter(
                    x=zs['x'] + zs['x'][::-1],
                    y=zs['y'] + [zs['y'][0]],
                    fill='toself',
                    fillcolor='rgba(69, 183, 209, 0.25)',
                    line=dict(color=self.colors['zs'], width=1, dash='dot'),
                    name=f'中枢_{i+1}',
                    showlegend=False
                ))
        
        # 添加线段 - 粗线显示
        if 'segment' in data and data['segment']:
            for seg in data['segment']:
                fig.add_trace(go.Scatter(
                    x=seg['x'],
                    y=seg['y'],
                    mode='lines',
                    name='线段',
                    line=dict(color=self.colors['seg'], width=2.5),
                    hoverinfo='y+name'
                ))
        
        # 添加买卖点 - 清晰标识
        if 'buy_sell_points' in data:
            for bsp in data['buy_sell_points']:
                color = self.colors['bsp_buy'] if bsp['is_buy'] else self.colors['bsp_sell']
                symbol = 'triangle-up' if bsp['is_buy'] else 'triangle-down'
                label = '买' if bsp['is_buy'] else '卖'
                
                fig.add_trace(go.Scatter(
                    x=[bsp['kl_idx']],
                    y=[bsp['price']],
                    mode='markers',
                    marker=dict(size=12, color=color, symbol=symbol, line=dict(width=2, color='white')),
                    name=f'{label}点',
                    hovertemplate=f"%{label}点 @ %{y:.2f}<extra></extra>"
                ))
        
        # 简洁布局 - 专注分析
        title_text = f"缠论分析 - {code}" if code else "缠论分析"
        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
                font=dict(size=16, family="SimHei")
            ),
            xaxis=dict(
                rangeslider=dict(visible=True),
                type='category',
                title="时间",
                showgrid=False
            ),
            yaxis=dict(
                title="价格",
                showgrid=True,
                gridcolor='lightgray'
            ),
            height=600,
            showlegend=True,
            template='plotly_white',
            hovermode='closest',
            margin=dict(l=50, r=20, t=60, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
