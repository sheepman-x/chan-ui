import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from .config_compiler import StreamlitConfig


class UIManager:
    """UI管理类，处理所有用户界面配置和交互逻辑"""
    
    def __init__(self, config_compiler: StreamlitConfig):
        self.config_compiler = config_compiler
        
    def setup_page_config(self):
        """设置页面配置"""
        st.set_page_config(
            page_title="缠论图表可视化",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def render_sidebar(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """渲染侧边栏，返回配置参数字典"""
        with st.sidebar:
            st.header("🔧 图表配置")
            st.markdown("---")
            
            # 资产信息配置
            asset_config = self._render_asset_config()
            
            # 时间配置
            date_config = self._render_time_config(asset_config.get('level', 'K_DAY'))
            
            # 缠论参数配置
            chan_params = self._render_chan_params()
            
            # 控制按钮
            refresh_requested = st.button("🔄 更新图表", type="primary", use_container_width=True)
            
            return {
                **asset_config,
                **date_config,
                'refresh_requested': refresh_requested
            }, chan_params
    
    def _render_asset_config(self) -> Dict[str, Any]:
        """渲染资产配置"""
        st.subheader("📊 资产信息")
        col1, col2 = st.columns(2)
        
        with col1:
            market_options = {
                "A股": {"prefix": "", "suffix": ".SZ", "example": "000002", "type": "stock"},
                "加密货币": {"prefix": "", "suffix": "", "example": "BTC/USDT", "type": "crypto"}
            }
            selected_market = st.selectbox(
                "资产类型", 
                options=list(market_options.keys()),
                help="选择资产类型"
            )
        
        with col2:
            market_config = market_options[selected_market]
            code = self._get_asset_code(market_config)
        
        # 时间级别选择
        level_options = self.config_compiler.get_available_levels()
        selected_level = st.selectbox(
            "时间级别", 
            options=list(level_options.keys()),
            index=list(level_options.keys()).index("K_DAY"),
            format_func=lambda x: level_options[x],
            help="选择K线时间周期"
        )
        
        return {
            'code': code,
            'level': selected_level,
            'market_type': market_config['type']
        }
    
    def _get_asset_code(self, market_config: Dict[str, str]) -> str:
        """获取资产代码"""
        if market_config["type"] == "crypto":
            crypto_options = ["BTC/USDT", "ETH/USDT"]
            selected_crypto = st.selectbox(
                "加密货币", 
                options=crypto_options,
                help="选择加密货币交易对"
            )
            
            if selected_crypto == "自定义":
                return st.text_input(
                    "自定义交易对", 
                    value="BTC/USDT",
                    help="输入加密货币交易对，例如：BTC/USDT"
                )
            return selected_crypto
        else:
            code_input = st.text_input(
                "股票代码", 
                value=market_config["example"],
                help=f"输入股票代码，例如：{market_config['example']}"
            )
            
            # 自动格式化A股代码
            if market_config["type"] == "stock" and not code_input.startswith("HK"):
                if code_input.startswith("00") or code_input.startswith("30"):
                    return f"{code_input}.SZ"
                elif code_input.startswith("60") or code_input.startswith("68"):
                    return f"{code_input}.SH"
                else:
                    return f"{code_input}.SZ"
            
            return f"{market_config['prefix']}{code_input}{market_config['suffix']}"
    
    def _render_time_config(self, level: str) -> Dict[str, str]:
        """渲染时间配置"""
        st.subheader("📅 时间范围")
        
        col1, col2 = st.columns(2)
        
        # 根据时间级别调整时间范围限制
        levels_map = {
            "K_1M": 7,
            "K_5M": 14,
            "K_15M": 30,
            "K_30M": 60,
            "K_60M": 120,
            "K_DAY": 365,
        }
        max_days_ago = levels_map[level]
        
        with col1:
            default_start = datetime.now() - timedelta(days=max_days_ago)
            start_date = st.date_input(
                "开始日期", 
                value=default_start,
                max_value=datetime.now(),
            )
        
        with col2:
            end_date = st.date_input(
                "结束日期", 
                value=datetime.now(),
                max_value=datetime.now()
            )
        
        return {
            'start_date': start_date.strftime("%Y-%m-%d"),
            'end_date': end_date.strftime("%Y-%m-%d")
        }
    
    def _render_chan_params(self) -> Dict[str, bool]:
        """渲染缠论参数配置"""
        st.markdown("---")
        st.subheader("📐 缠论参数")
        
        with st.expander("📋 基础参数", expanded=True):
            return {
                "bi_strict": st.checkbox("严格笔", value=True, help="使用严格的笔定义"),
                "zs_combine": st.checkbox("中枢合并", value=True, help="合并相邻中枢"),
                "show_bsp": st.checkbox("显示买卖点", value=True),
                "show_bi": st.checkbox("显示笔", value=True),
                "show_seg": st.checkbox("显示线段", value=True),
                "show_zs": st.checkbox("显示中枢", value=True)
            }
    
    def render_main_content(self):
        """渲染主内容区域"""
        st.title("📈 缠论图表可视化")
        
        # 使用说明
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
    
    def render_chart_section(self, chart_service, config, chan_params):
        """渲染图表区域"""
        tab1, tab2 = st.tabs(["📊 图表展示", "🔍 数据信息"])
        
        with tab1:
            if st.button("🚀 生成/更新图表", type="primary", use_container_width=True):
                chart_service.generate_chart(
                    code=config['code'],
                    level=config['level'],
                    start_date=config['start_date'],
                    end_date=config['end_date'],
                    chan_params=chan_params
                )
                
            if chart_service.has_chart():
                chart_service.display_chart()
                chart_service.display_update_time()
            else:
                st.info("🎯 欢迎使用缠论图表可视化工具！")
                st.info("👈 请在左侧配置参数后，点击'生成图表'按钮")
        
        with tab2:
            if chart_service.has_chart():
                chart_service.display_data_summary()
            else:
                st.info("📊 生成图表后可查看数据统计信息")