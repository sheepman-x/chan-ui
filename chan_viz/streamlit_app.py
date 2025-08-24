import streamlit as st
import sys
sys.path.append('../chan.py')

# 页面配置
st.set_page_config(
    page_title="缠论图表", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 头部信息
st.title("📊 缠论图表可视化")
st.markdown("### 第一条K线，第一次缠论可视化")

# 侧边栏初始化
with st.sidebar:
    st.header("参数配置🔧")
    
    # 资产代码选择
    asset_type = st.radio("资产类型", ["股票", "加密货币"], horizontal=True)
    
    if asset_type == "股票":
        # 股票代码输入
        code = st.text_input("股票代码", value="HK.00700", 
                           help="支持格式: 600036.SH, 000001.SZ, HK.00700")
    else:
        # 加密货币选择
        crypto_options = ["BTC/USDT", "ETH/USDT", "BTC/USD", "ETH/USD"]
        code = st.selectbox("加密货币", options=crypto_options)
    
    # 时间级别选择
    level_options = ["K_1M", "K_5M", "K_15M", "K_30M", "K_60M", "K_DAY"]
    selected_level = st.select_slider("时间级别", options=level_options)
    
    # 日期范围
    start_date = st.date_input("开始日期")
    end_date = st.date_input("结束日期")
    
    # 实时参数控制
    st.subheader("缠论参数")
    bi_strict = st.checkbox("严格笔", value=True)
    zs_combine = st.checkbox("中枢合并", value=True)
    
    # 一键计算按钮
    if st.button("🔄 生成图表", type="primary"):
        st.session_state.calculated = True

# 主显示区域
if st.session_state.get('calculated'):
    st.success("✅ 计算成功！显示缠论图表...")
else:
    st.info("👈 请在左侧配置参数后点击'生成图表'")