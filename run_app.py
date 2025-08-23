import streamlit as st
import sys
from datetime import datetime, timedelta
import os

# 动态添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'chan.py'))

# 导入自定义模块
from chan_viz.config_compiler import StreamlitConfig
from chan_viz.data_service import StreamlitDataService
from chan_viz.chart_render import PlotlyChartRenderer

# 初始化服务
config_compiler = StreamlitConfig()
data_service = StreamlitDataService()
chart_renderer = PlotlyChartRenderer()

# 设置页面配置
st.set_page_config(
    page_title="缠论图表可视化",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """主应用入口"""
    
    # 侧边栏配置
    with st.sidebar:
        st.header("🔧 图表配置")
        st.markdown("---")
        
        # 基础信息
        st.subheader("📊 股票信息")
        col1, col2 = st.columns(2)
        with col1:
            code = st.text_input("股票代码", value="002415.SZ", 
                               help="例如：002415.SZ 或 HK.00700")
        with col2:
            level_options = config_compiler.get_available_levels()
            selected_level = st.selectbox("时间级别", 
                                        options=list(level_options.keys()),
                                        format_func=lambda x: level_options[x],
                                        help="选择K线时间周期")
        
        # 时间设置
        st.subheader("📅 时间范围")
        col1, col2 = st.columns(2)
        with col1:
            default_start = datetime.now() - timedelta(days=365)
            start_date = st.date_input("开始日期", 
                                     value=default_start,
                                     max_value=datetime.now())
        with col2:
            end_date = st.date_input("结束日期", 
                                   value=datetime.now(),
                                   max_value=datetime.now())
        
        st.markdown("---")
        
        # 缠论参数
        st.subheader("📐 缠论参数")
        
        with st.expander("📋 基础参数", expanded=True):
            config_params = {
                "bi_strict": st.checkbox("严格笔", value=True, 
                                       help="使用严格的笔定义"),
                "zs_combine": st.checkbox("中枢合并", value=True, 
                                        help="合并相邻中枢"),
                "show_bsp": st.checkbox("显示买卖点", value=True),
                "show_bi": st.checkbox("显示笔", value=True),
                "show_seg": st.checkbox("显示线段", value=True),
                "show_zs": st.checkbox("显示中枢", value=True)
            }
        
        st.markdown("---")
        
        # 控制按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 更新图表", type="primary", use_container_width=True):
                st.session_state.refresh_chart = True
        with col2:
            if st.button("🧹 清空缓存", use_container_width=True):
                st.cache_data.clear()
                st.success("缓存已清空!")
    
    # 主要内容区域
    st.title("📈 缠论图表可视化")
    st.markdown("### 第一条K线，第一次缠论可视化")
    
    # 使用tabs组织内容
    tab1, tab2, tab3 = st.tabs(["📊 图表展示", "📝 使用说明", "🔍 数据信息"])
    
    with tab1:
        if st.button("🚀 生成/更新图表", type="primary", use_container_width=True) or st.session_state.get('refresh_chart'):
            try:
                with st.spinner("📊 正在加载缠论数据..."):
                    # 转换配置
                    chan_config = config_compiler.from_streamlit(config_params)
                    
                    # 日期格式转换
                    start_str = start_date.strftime("%Y-%m-%d")
                    end_str = end_date.strftime("%Y-%m-%d")
                    
                    # 获取数据
                    data = data_service.load_chan_data(
                        code=code,
                        level=selected_level,
                        config=chan_config,
                        start_date=start_str,
                        end_date=end_str
                    )
                    
                    # 生成图表
                    fig = chart_renderer.create_chan_chart(data, selected_level, code)
                    st.session_state.chart_figure = fig
                    st.session_state.chart_data = data
                    st.session_state.last_update = datetime.now()
                    st.session_state.refresh_chart = False
                    
            except Exception as e:
                st.error(f"❌ 计算出错: {str(e)}")
                st.exception(e)
        
        # 显示图表
        if 'chart_figure' in st.session_state:
            st.subheader(f"📊 {code} - {config_compiler.get_available_levels()[selected_level]}")
            
            # 图表控制选项
            col1, col2, col3 = st.columns(3)
            with col1:
                chart_height = st.slider("图表高度", min_value=400, max_value=1200, value=800, step=50)
            with col2:
                show_volume = st.checkbox("显示成交量", value=True)
            with col3:
                auto_range = st.checkbox("自动范围", value=True)
            
            st.plotly_chart(
                st.session_state.chart_figure,
                use_container_width=True,
                height=chart_height,
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                    'scrollZoom': True
                }
            )
            
            # 显示刷新时间
            if 'last_update' in st.session_state:
                st.caption(f"📅 最后更新: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            # 显示演示图表
            st.info("🎯 欢迎使用缠论图表可视化工具！")
            st.info("👈 请在左侧配置参数后，点击'生成图表'按钮")
            st.markdown("### 简化说明")
            st.markdown(""")
            📈 **核心功能**：
            - 直接调用chan.py缠论算法
            - 显示：K线、笔、中枢、线段、买卖点
            - 无成交量、无动画、专注指标
            """)
    
    with tab2:
        st.markdown("""
        ### 📚 使用说明
        
        **1. 基本操作**
        - 在左侧侧边栏输入股票代码
        - 选择合适的时间级别
        - 设置时间范围
        - 调整缠论参数
        
        **2. 缠论概念**
        - **笔**: 识别趋势的最小单位
        - **线段**: 由笔组成的更大级别趋势
        - **中枢**: 价格震荡的区间
        - **买卖点**: 基于缠论理论的关键交易点
        
        **3. 图表交互**
        - 鼠标悬停查看详细信息
        - 拖拽缩放查看局部细节
        - 双击图表重置视图
        """)
    
    with tab3:
        if 'chart_data' in st.session_state:
            st.markdown("### 📊 数据概览")
            data = st.session_state.chart_data
            
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
        
    # 底部信息
    st.divider()
    st.markdown("---")
    
    st.caption("💡 系统信息")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📡 支持级别", "6个", "完整")
    with col2:
        st.metric("⚙️ 参数选项", "6个", "灵活")
    with col3:
        st.metric("🔍 元素类型", "4种", "全面")
    with col4:
        st.metric("💾 缓存时间", "1小时", "高效")

if __name__ == "__main__":
    main()