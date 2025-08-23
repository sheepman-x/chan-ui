import plotly.graph_objects as go
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
        
        # 获取日期列表用于索引映射
        dates = data['kline']['dates']
        
        # 添加K线图
        fig.add_trace(go.Candlestick(
            x=dates,
            open=data['kline']['open'],
            high=data['kline']['high'],
            low=data['kline']['low'],
            close=data['kline']['close'],
            name='K线',
            increasing_line_color='red',  # A股红色上涨
            decreasing_line_color='green',
            showlegend=True
        ))
        
        # 添加笔的图例项（只添加一次）
        if 'bi' in data and data['bi']:
            # 添加笔的图例
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='lines+markers',
                name='笔',
                line=dict(color=self.colors['bi'], width=1.5),
                marker=dict(size=4),
                showlegend=True
            ))
            
            # 添加具体的笔数据
            for i, bi in enumerate(data['bi']):
                # 将索引映射为日期
                x_indices = bi['x']
                x_dates = [dates[idx] for idx in x_indices if idx < len(dates)]
                
                if len(x_dates) == len(bi['y']):  # 确保坐标对应
                    fig.add_trace(go.Scatter(
                        x=x_dates,
                        y=bi['y'],
                        mode='lines+markers',
                        line=dict(color=self.colors['bi'], width=1.5),
                        marker=dict(size=4),
                        hovertemplate="笔: %{y:.2f}<br>日期: %{x}<extra></extra>",
                        showlegend=False  # 不在图例中显示具体笔
                    ))
        
        # 添加线段的图例项（只添加一次）
        if 'segment' in data and data['segment']:
            # 添加线段的图例
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='lines',
                name='线段',
                line=dict(color=self.colors['seg'], width=2.5),
                showlegend=True
            ))
            
            # 添加具体的线段数据
            for i, seg in enumerate(data['segment']):
                # 将索引映射为日期
                x_indices = seg['x']
                x_dates = [dates[idx] for idx in x_indices if idx < len(dates)]
                
                if len(x_dates) == len(seg['y']):  # 确保坐标对应
                    fig.add_trace(go.Scatter(
                        x=x_dates,
                        y=seg['y'],
                        mode='lines',
                        line=dict(color=self.colors['seg'], width=2.5),
                        hovertemplate="线段: %{y:.2f}<br>日期: %{x}<extra></extra>",
                        showlegend=False  # 不在图例中显示具体线段
                    ))
        
        # 添加中枢的图例项（只添加一次）
        if 'central_zone' in data and data['central_zone']:
            # 添加中枢的图例
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='lines',
                name='中枢',
                line=dict(color=self.colors['zs'], width=1, dash='dot'),
                fill='toself',
                fillcolor='rgba(69, 183, 209, 0.25)',
                showlegend=True
            ))
            
            # 添加具体的中枢数据
            for i, zs in enumerate(data['central_zone']):
                # 将索引映射为日期
                x_indices = zs['x']
                if len(x_indices) >= 2 and all(idx < len(dates) for idx in x_indices):
                    x_start, x_end = dates[x_indices[0]], dates[x_indices[1]]
                    y_low, y_high = zs['y'][0], zs['y'][1]
                    
                    # 创建矩形区域
                    fig.add_trace(go.Scatter(
                        x=[x_start, x_end, x_end, x_start, x_start],
                        y=[y_low, y_low, y_high, y_high, y_low],
                        fill='toself',
                        fillcolor='rgba(69, 183, 209, 0.25)',
                        line=dict(color=self.colors['zs'], width=1, dash='dot'),
                        hovertemplate=f"中枢 {i+1}<br>范围: {y_low:.2f} - {y_high:.2f}<extra></extra>",
                        showlegend=False  # 不在图例中显示具体中枢
                    ))
        
        # 添加买卖点的图例项（只添加一次）
        if 'buy_sell_points' in data and data['buy_sell_points']:
            # 添加买点图例
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                name='买点',
                marker=dict(size=12, color=self.colors['bsp_buy'], symbol='triangle-up', line=dict(width=2, color='white')),
                showlegend=True
            ))
            
            # 添加卖点图例
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                name='卖点',
                marker=dict(size=12, color=self.colors['bsp_sell'], symbol='triangle-down', line=dict(width=2, color='white')),
                showlegend=True
            ))
            
            # 添加具体的买卖点数据
            for i, bsp in enumerate(data['buy_sell_points']):
                # 将索引映射为日期
                kl_idx = bsp['kl_idx']
                if kl_idx < len(dates):
                    x_date = dates[kl_idx]
                    color = self.colors['bsp_buy'] if bsp['is_buy'] else self.colors['bsp_sell']
                    symbol = 'triangle-up' if bsp['is_buy'] else 'triangle-down'
                    label = '买' if bsp['is_buy'] else '卖'
                    
                    fig.add_trace(go.Scatter(
                        x=[x_date],
                        y=[bsp['price']],
                        mode='markers',
                        marker=dict(size=12, color=color, symbol=symbol, line=dict(width=2, color='white')),
                        hovertemplate=f"{label}点<br>价格: %{{y:.2f}}<br>日期: %{{x}}<extra></extra>",
                        showlegend=False  # 不在图例中显示具体买卖点
                    ))
        
        # 简洁布局 - 去掉多余控件，只保留主图和图例
        title_text = f"缠论分析 - {code}" if code else "缠论分析"
        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
                font=dict(size=16, family="SimHei")
            ),
            xaxis=dict(
                rangeslider=dict(visible=False),  # 去掉slide控件
                type='category',
                title="时间",
                showgrid=False,
                fixedrange=True  # 禁用缩放
            ),
            yaxis=dict(
                title="价格",
                showgrid=True,
                gridcolor='lightgray',
                fixedrange=True  # 禁用缩放
            ),
            height=600,
            showlegend=True,
            template='plotly_white',
            hovermode='closest',
            margin=dict(l=50, r=20, t=60, b=50),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # 去掉工具栏，只保留基本功能
        fig.update_layout(
            modebar=dict(
                remove=['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomin2d', 'zoomout2d', 'autoScale2d', 'resetScale2d']
            )
        )
        
        return fig
    
