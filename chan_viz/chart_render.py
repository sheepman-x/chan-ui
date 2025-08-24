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
                    # 根据is_sure决定线型：确定的笔用实线，不确定的用虚线
                    is_sure = bi.get('is_sure', True)
                    line_style = dict(color=self.colors['bi'], width=1.5)
                    if not is_sure:
                        line_style['dash'] = 'dash'
                    
                    fig.add_trace(go.Scatter(
                        x=x_dates,
                        y=bi['y'],
                        mode='lines+markers',
                        line=line_style,
                        marker=dict(size=4),
                        hovertemplate="笔: %{y:.2f}<br>日期: %{x}<br>状态: %{customdata}<extra></extra>",
                        customdata=["确定" if is_sure else "不确定"],
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
                    # 根据is_sure决定线型：确定的线段用实线，不确定的用虚线
                    is_sure = seg.get('is_sure', True)
                    line_style = dict(color=self.colors['seg'], width=2.5)
                    if not is_sure:
                        line_style['dash'] = 'dash'
                    
                    fig.add_trace(go.Scatter(
                        x=x_dates,
                        y=seg['y'],
                        mode='lines',
                        line=line_style,
                        hovertemplate="线段: %{y:.2f}<br>日期: %{x}<br>状态: %{customdata}<extra></extra>",
                        customdata=["确定" if is_sure else "不确定"],
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
                    
                    # 根据is_sure决定线型：确定的中枢用点线，不确定的用虚线
                    is_sure = zs.get('is_sure', True)
                    line_style = dict(color=self.colors['zs'], width=1)
                    if is_sure:
                        line_style['dash'] = 'dot'  # 确定的中枢用点线
                    else:
                        line_style['dash'] = 'dash'  # 不确定的中枢用虚线
                    
                    # 创建矩形区域
                    fig.add_trace(go.Scatter(
                        x=[x_start, x_end, x_end, x_start, x_start],
                        y=[y_low, y_low, y_high, y_high, y_low],
                        fill='toself',
                        fillcolor='rgba(69, 183, 209, 0.25)',
                        line=line_style,
                        hovertemplate=f"中枢 {i+1}<br>范围: {y_low:.2f} - {y_high:.2f}<br>状态: {'确定' if is_sure else '不确定'}<extra></extra>",
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
            
            # 添加买卖点类型图例
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='text',
                name='一类买卖点',
                textfont=dict(size=10, color='black'),
                showlegend=True
            ))
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='text', 
                name='二类买卖点',
                textfont=dict(size=10, color='black'),
                showlegend=True
            ))
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='text',
                name='三类买卖点',
                textfont=dict(size=10, color='black'),
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
                    
                    # 使用chan.py风格的买卖点显示
                    bsp_type = bsp.get('type', '')
                    marker_size, marker_symbol = self._get_bsp_marker_style(bsp_type, bsp['is_buy'])
                    chan_style_label = self._get_bsp_chan_style_label(bsp_type, bsp['is_buy'])
                    
                    # 计算买卖点偏移位置，远离K线
                    price_offset = self._calculate_price_offset(data['kline'], bsp['price'], bsp['is_buy'])
                    
                    # 添加买卖点标记
                    fig.add_trace(go.Scatter(
                        x=[x_date],
                        y=[bsp['price'] + price_offset],
                        mode='markers',
                        marker=dict(size=marker_size, color=color, symbol=marker_symbol, line=dict(width=2, color='white')),
                        hovertemplate=f"{label}点 ({bsp_type})<br>价格: %{{y:.2f}}<br>日期: %{{x}}<extra></extra>",
                        showlegend=False
                    ))
                    
                    # 添加买卖点文本标签（放在标记右侧）
                    # 使用textposition控制位置，Plotly会自动处理偏移
                    fig.add_trace(go.Scatter(
                        x=[x_date],
                        y=[bsp['price'] + price_offset],
                        mode='text',
                        text=[chan_style_label],
                        textposition='middle right',  # 文本放在标记右侧
                        textfont=dict(size=13, color='black', family='Arial Bold'),  # 黑色文字，更大字体
                        showlegend=False
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
    
    def _get_bsp_chan_style_label(self, bsp_type, is_buy):
        """获取chan.py风格的买卖点标签"""
        if not bsp_type:
            return "b?" if is_buy else "s?"
        
        # 直接使用chan.py的格式: b1, s2, b2,3b 等
        prefix = "b" if is_buy else "s"
        return f"  {prefix}{bsp_type}"
    
    def _get_bsp_marker_style(self, bsp_type, is_buy):
        """根据买卖点类型获取chan.py风格的标记样式"""
        # chan.py使用统一的三角形标记，通过文本区分类型
        # 这里我们保持一致的三角形样式，通过大小稍微区分
        if '1' in bsp_type:
            return 14, 'triangle-up' if is_buy else 'triangle-down'  # 一类买卖点稍大
        elif '2' in bsp_type:
            return 12, 'triangle-up' if is_buy else 'triangle-down'  # 二类买卖点标准
        elif '3' in bsp_type:
            return 10, 'triangle-up' if is_buy else 'triangle-down'  # 三类买卖点稍小
        else:
            return 12, 'triangle-up' if is_buy else 'triangle-down'  # 默认
    
    def _calculate_price_offset(self, kline_data, price, is_buy):
        """计算买卖点价格偏移量，使其远离K线"""
        # 计算价格范围
        min_price = min(kline_data['low'])
        max_price = max(kline_data['high'])
        price_range = max_price - min_price
        
        # 计算偏移量（价格范围的5%）
        offset_percentage = 0.05
        offset = price_range * offset_percentage
        
        # 买点向下偏移，卖点向上偏移（远离K线主体）
        return -offset if is_buy else offset
    
