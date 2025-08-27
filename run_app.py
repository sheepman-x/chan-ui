import streamlit as st
import sys
import os
import subprocess

# 检查chan.py子模块是否存在且不为空
current_dir = os.path.dirname(__file__) or os.getcwd()
chan_path = os.path.join(current_dir, 'chan.py')
if not os.path.exists(chan_path) or not os.listdir(chan_path):
    st.warning("⚠️ chan.py子模块未初始化，正在下载...")
    try:
        # 初始化并更新子模块
        result = subprocess.run(["git", "submodule", "update", "--init", "--recursive"], 
                              capture_output=True, text=True, cwd=current_dir)
        if result.returncode == 0:
            st.success("✅ chan.py子模块下载完成")
        else:
            st.error(f"❌ 子模块下载失败: {result.stderr}")
            st.stop()
    except Exception as e:
        st.error(f"❌ 子模块初始化异常: {str(e)}")
        st.stop()

# 动态添加项目路径
sys.path.insert(0, chan_path)

# 导入新创建的模块
from chan_viz.config_compiler import StreamlitConfig
from chan_viz.data_service import StreamlitDataService
from chan_viz.chart_render import PlotlyChartRenderer
from chan_viz.ui_manager import UIManager
from chan_viz.chart_service import ChartService

# 初始化服务
config_compiler = StreamlitConfig()
data_service = StreamlitDataService()
chart_renderer = PlotlyChartRenderer()

# 创建UI管理器和图表服务
ui_manager = UIManager(config_compiler)
chart_service = ChartService(config_compiler, data_service, chart_renderer)

def main():
    """简化后的主应用入口"""
    
    # 设置页面配置
    ui_manager.setup_page_config()
    
    # 渲染侧边栏并获取配置
    config, chan_params = ui_manager.render_sidebar()
    
    # 更新会话状态
    st.session_state.update({
        'selected_level': config['level'],
        'selected_code': config['code']
    })
    
    # 处理刷新请求
    if config.get('refresh_requested') or st.session_state.get('refresh_chart'):
        chart_service.generate_chart(
            code=config['code'],
            level=config['level'],
            start_date=config['start_date'],
            end_date=config['end_date'],
            chan_params=chan_params
        )
        st.session_state.refresh_chart = False
    
    # 渲染主内容区域
    ui_manager.render_main_content()
    ui_manager.render_chart_section(chart_service, config, chan_params)

if __name__ == "__main__":
    main()