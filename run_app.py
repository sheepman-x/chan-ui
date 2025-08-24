import streamlit as st
import sys
from datetime import datetime, timedelta
import os

# 动态添加项目路径
chan_path = os.path.join(os.path.dirname(__file__), 'chan.py')
sys.path.append(chan_path)

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
            market_options = {
                "A股": {"prefix": "", "suffix": ".SZ", "example": "000002"},
                # "港股": {"prefix": "HK.", "suffix": "", "example": "00700"}, 
                # "美股": {"prefix": "", "suffix": "", "example": "AAPL"}
            }
            selected_market = st.selectbox("股票市场", 
                                         options=list(market_options.keys()),
                                         help="选择股票所属市场（目前仅支持A股）")
        with col2:
            market_config = market_options[selected_market]
            code_input = st.text_input("股票代码", 
                                     value=market_config["example"],
                                     help=f"输入{selected_market}代码，例如：{market_config['example']}")
            
        # 根据市场自动格式化股票代码
        if selected_market == "A股":
            if code_input.startswith("00") or code_input.startswith("30"):
                code = f"{code_input}.SZ"  # 深交所
            elif code_input.startswith("60") or code_input.startswith("68"):
                code = f"{code_input}.SH"  # 上交所
            else:
                code = f"{code_input}.SZ"  # 默认深交所
        else:
            # 其他市场的格式化逻辑（预留）
            code = f"{market_config['prefix']}{code_input}{market_config['suffix']}"
        
        # 时间级别选择
        level_options = config_compiler.get_available_levels()
        selected_level = st.selectbox("时间级别", 
                                    options=list(level_options.keys()),
                                    index=list(level_options.keys()).index("K_DAY"),
                                    format_func=lambda x: level_options[x],
                                    help="选择K线时间周期")
        
        # 时间设置
        st.subheader("📅 时间范围")
        
        # 根据时间级别动态调整时间范围限制
        intraday_levels = ["K_1M", "K_5M", "K_15M", "K_30M", "K_60M"]
        is_intraday = selected_level in intraday_levels
        
        col1, col2 = st.columns(2)
        with col1:
            if is_intraday:
                # 分钟级别限制在30天内
                max_days_ago = 30
                default_start = datetime.now() - timedelta(days=max_days_ago)
                min_date = datetime.now() - timedelta(days=max_days_ago)
                start_date = st.date_input("开始日期", 
                                         value=default_start,
                                         min_value=min_date,
                                         max_value=datetime.now(),
                                         help=f"分钟级别数据限制在最近{max_days_ago}天内")
            else:
                # 日线级别可以选择更长时间范围
                max_days_ago = 600
                default_start = datetime.now() - timedelta(days=max_days_ago)
                start_date = st.date_input("开始日期", 
                                         value=default_start,
                                         max_value=datetime.now())
        with col2:
            end_date = st.date_input("结束日期", 
                                   value=datetime.now(),
                                   max_value=datetime.now())
        
        # 对分钟级别进行时间范围检查
        if is_intraday:
            date_range = (end_date - start_date).days
            if date_range > 30:
                st.warning(f"⚠️ 分钟级别数据建议时间范围不超过30天，当前为{date_range}天")
                st.info("💡 较长时间范围可能导致数据量过大，影响页面性能")
        
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
        if st.button("🔄 更新图表", type="primary", use_container_width=True):
            st.session_state.refresh_chart = True
    
    # 主要内容区域
    st.title("📈 缠论图表可视化")
    
    # 使用说明放在顶部
    with st.expander("📚 使用说明", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **基本操作**
            - 左侧选择股票市场和代码
            - 选择时间级别（默认日线）
            - 设置时间范围
            - 调整缠论参数后点击生成图表
            """)
        with col2:
            st.markdown("""
            **缠论概念**
            - **笔**: 识别趋势的最小单位
            - **线段**: 由笔组成的更大级别趋势  
            - **中枢**: 价格震荡的区间
            - **买卖点**: 基于缠论理论的关键交易点
            """)
    
    # 使用tabs组织内容
    tab1, tab2 = st.tabs(["📊 图表展示", "🔍 数据信息"])
    
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
            
            # 直接显示图表，不再提供额外的控制选项
            st.plotly_chart(
                st.session_state.chart_figure,
                use_container_width=True,
                config={
                    'displayModeBar': False,  # 完全隐藏工具栏
                    'displaylogo': False,
                    'staticPlot': False  # 保留hover交互
                }
            )
            
            # 显示刷新时间
            if 'last_update' in st.session_state:
                st.caption(f"📅 最后更新: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            # 显示演示图表
            st.info("🎯 欢迎使用缠论图表可视化工具！")
            st.info("👈 请在左侧配置参数后，点击'生成图表'按钮")
    
    with tab2:
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
        else:
            st.info("📊 生成图表后可查看数据统计信息")

if __name__ == "__main__":
    main()