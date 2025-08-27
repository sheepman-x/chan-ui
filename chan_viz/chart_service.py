import streamlit as st
from datetime import datetime
from typing import Dict, Any
from .data_service import StreamlitDataService
from .chart_render import PlotlyChartRenderer
from .config_compiler import StreamlitConfig


class ChartService:
    """图表服务类，封装数据获取和图表生成逻辑"""
    
    def __init__(self, config_compiler: StreamlitConfig, 
                 data_service: StreamlitDataService, 
                 chart_renderer: PlotlyChartRenderer):
        self.config_compiler = config_compiler
        self.data_service = data_service
        self.chart_renderer = chart_renderer
        
    def generate_chart(self, code: str, level: str, start_date: str, 
                      end_date: str, chan_params: Dict[str, bool]):
        """生成图表"""
        try:
            with st.spinner("📊 正在加载缠论数据..."):
                # 转换配置
                chan_config = self.config_compiler.from_streamlit(chan_params)
                
                # 获取数据
                data = self.data_service.load_chan_data(
                    code=code,
                    level=level,
                    config=chan_config,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # 生成图表
                fig = self.chart_renderer.create_chan_chart(data, level, code)
                
                # 存储会话数据
                st.session_state.chart_figure = fig
                st.session_state.chart_data = data
                st.session_state.last_update = datetime.now()
                
        except Exception as e:
            st.error(f"❌ 计算出错: {str(e)}")
            st.exception(e)
    
    def has_chart(self) -> bool:
        """检查是否有图表数据"""
        return 'chart_figure' in st.session_state
    
    def display_chart(self):
        """显示图表"""
        if not self.has_chart():
            return
            
        level_options = self.config_compiler.get_available_levels()
        selected_level = st.session_state.get('selected_level', 'K_DAY')
        code = st.session_state.get('selected_code', '')
        
        st.subheader(f"📊 {code} - {level_options[selected_level]}")
        
        st.plotly_chart(
            st.session_state.chart_figure,
            use_container_width=True,
            config={
                'displayModeBar': False,
                'displaylogo': False,
                'staticPlot': False
            }
        )
    
    def display_update_time(self):
        """显示最后更新时间"""
        if 'last_update' in st.session_state:
            st.caption(f"📅 最后更新: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def display_data_summary(self):
        """显示数据摘要"""
        if 'chart_data' not in st.session_state:
            return
            
        data = st.session_state.chart_data
        
        st.markdown("### 📊 数据概览")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 K线数量", len(data['kline']['dates']))
        with col2:
            st.metric("✏️ 笔数量", len(data.get('bi', [])))
        with col3:
            st.metric("🏛️ 中枢数量", len(data.get('central_zone', [])))
        with col4:
            st.metric("🎯 买卖点数量", len(data.get('buy_sell_points', [])))
        
        if st.checkbox("显示原始数据"):
            st.json(data)