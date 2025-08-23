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
        """创建缠论图表"""
        
        # 1. 创建基础图形
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(f'缠论图表 - {level}', '交易量'),
            row_heights=[0.7, 0.3]
        )
        
        # 2. 添加K线图
        fig.add_trace(go.Candlestick(
            x=data['kline']['dates'],
            open=data['kline']['open'],
            high=data['kline']['high'],
            low=data['kline']['low'],
            close=data['kline']['close'],
            name='K线',
            increasing_line_color='red',  # A股红色上涨
            decreasing_line_color='green',
            increasing_fillcolor='red',
            decreasing_fillcolor='green'
        ), row=1, col=1)
        
        # 3. 添加笔
        if 'bi' in data and data['bi']:
            for bi in data['bi']:
                fig.add_trace(go.Scatter(
                    x=bi['x'],
                    y=bi['y'],
                    mode='lines+markers',
                    name='笔',
                    line=dict(color=self.colors['bi'], width=2),
                    hovertext=f"类型: {bi['type']}, 方向: {bi['direction']}" if bi.get('direction') else "笔"
                ), row=1, col=1)
        
        # 4. 添加中枢
        if 'central_zone' in data:
            for zs in data['central_zone']:
                fig.add_trace(go.Scatter(
                    x=zs['x'] + zs['x'][::-1],
                    y=zs['y'] + [zs['y'][0]],  # 闭合矩形
                    fill='toself',
                    fillcolor='rgba(69, 183, 209, 0.2)',
                    line=dict(color=self.colors['zs'], width=1),
                    name='中枢',
                    opacity=0.8
                ), row=1, col=1)
        
        # 5. 添加线段
        if 'segment' in data and data['segment']:
            for seg in data['segment']:
                fig.add_trace(go.Scatter(
                    x=seg['x'],
                    y=seg['y'],
                    mode='lines',
                    name='线段',
                    line=dict(color=self.colors['seg'], width=3, dash='dash'),
                    hovertext=seg.get('type', '线段')
                ), row=1, col=1)
        
        # 6. 添加买卖点
        if 'buy_sell_points' in data:
            for bsp in data['buy_sell_points']:
                color = self.colors['bsp_buy'] if bsp['is_buy'] else self.colors['bsp_sell']
                symbol = 'triangle-up' if bsp['is_buy'] else 'triangle-down'
                
                fig.add_trace(go.Scatter(
                    x=[bsp['kl_idx']],
                    y=[bsp['price']],
                    mode='markers',
                    marker=dict(size=15, color=color, symbol=symbol, line=dict(width=2, color='white')),
                    name='买点' if bsp['is_buy'] else '卖点',
                    hovertext=bsp.get('type', '买卖点')
                ), row=1, col=1)
        
        # 7. 添加交易量
        volume_data = [abs(o-c) * 1000 for o, c in zip(data['kline']['open'], data['kline']['close'])]
        fig.add_trace(go.Bar(
            name='成交量',
            x=data['kline']['dates'],
            y=volume_data,
            marker_color='lightblue',
            opacity=0.7
        ), row=2, col=1)
        
        # 8. 设置布局
        title_text = f"缠论技术分析 - {code}" if code else "缠论技术分析"
        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
                font=dict(size=24, family="Arial Black")
            ),
            xaxis=dict(
                rangeslider=dict(visible=True),
                type='category',
                title="时间"
            ),
            xaxis2=dict(title="时间"),
            yaxis=dict(title="价格 (元)"),
            yaxis2=dict(title="成交量"),
            height=800,
            showlegend=True,
            template='plotly_white',
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="black",
                borderwidth=1
            )
        )
        
        return fig
    
    def create_animated_chart(self, data_snapshot_list):
        """创建回放动画图表"""
        frames = []
        for snapshot in data_snapshot_list:
            frame = go.Frame(data=[
                go.Candlestick(x=snapshot['dates'], **snapshot['ohlc']),
                go.Scatter(x=snapshot['bi']['x'], y=snapshot['bi']['y'])
            ])
            frames.append(frame)
            
        fig = go.Figure(
            data=frames[-1]['data'] if frames else [],
            frames=frames,
            layout=go.Layout(
                updatemenus=[{
                    "buttons": [
                        {
                            "args": [None, {"frame": {"duration": 500, "redraw": True}}],
                            "label": "▶️ 开始回放",
                            "method": "animate"
                        },
                        {
                            "args": [[None], {"frame": {"duration": 0, "redraw": False}}],
                            "label": "⏸️ 暂停",
                            "method": "animate"
                        }
                    ]
                }]
            )
        )
        
        return fig
    
    def create_simple_mock_chart(self) -> go.Figure:
        """创建简单的模拟图表用于测试"""
        import numpy as np
        from datetime import datetime, timedelta
        
        # 生成模拟数据
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
        dates.reverse()
        
        # 模拟K线数据
        np.random.seed(42)
        base_price = 100
        open_prices = [base_price]
        close_prices = [base_price]
        highs = [base_price + 2]
        lows = [base_price - 2]
        
        for i in range(1, 30):
            prev_close = close_prices[-1]
            change = np.random.uniform(-5, 5)
            open_prices.append(prev_close)
            close_prices.append(prev_close + change)
            high = max(open_prices[-1], close_prices[-1]) + abs(np.random.uniform(0, 2))
            low = min(open_prices[-1], close_prices[-1]) - abs(np.random.uniform(0, 2))
            highs.append(high)
            lows.append(low)
        
        # 创建图表
        fig = go.Figure(data=[go.Candlestick(
            x=dates,
            open=open_prices,
            high=highs,
            low=lows,
            close=close_prices,
            name='K线'
        )])
        
        # 添加模拟的缠论元素
        bi_data = [
            {"x": [5, 10], "y": [95, 105], "label": "上升笔"},
            {"x": [12, 18], "y": [105, 98], "label": "下降笔"}
        ]
        
        for bi in bi_data:
            fig.add_trace(go.Scatter(
                x=bi["x"],
                y=bi["y"],
                mode='lines+markers',
                name=bi["label"],
                line=dict(color=self.colors['bi'], width=2)
            ))
        
        fig.update_layout(
            title='缠论图表（演示数据）',
            xaxis_title='日期',
            yaxis_title='价格',
            height=600,
            template='plotly_white'
        )
        
        return fig