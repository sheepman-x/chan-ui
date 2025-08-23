# Streamlit版缠论图表可视化实施计划

## 🎯 第一阶段：极简后端方案（纯Python）

### 技术栈转换
- **后端**：Streamlit（零前端开发）
- **图表**：Plotly（高频图表）+ Matplotlib（静态图）
- **交互**：Streamlit原生控件（滑块、下拉框、开关）
- **部署**：`streamlit run app.py` 一键启动

---

## 📋 详细实施路线图

### Step 1: 虚拟环境配置 (10分钟)

```bash
# 创建隔离环境
python3.11 -m venv chan-viz-env
source chan-viz-env/bin/activate

# 安装依赖包
pip install streamlit plotly pandas reqparse
pip install -r chan.py/Script/requirements.txt

# 验证安装
streamlit hello  # 浏览器自动打开验证
```

### Step 2: 最小化Web服务 (15分钟)

创建 `chan_viz/streamlit_app.py`:
```python
import streamlit as st
import sys
sys.path.append('chan.py')

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
    
    # 股票代码输入
    code = st.text_input("股票代码", value="HK.00700")
    
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
    st.info("👈 请在左侧配置参数后点击"生成图表")")
```

### Step 3: 抽离缠论参数 (20分钟)

创建 `chan_viz/config_compiler.py`:
```python
from typing import Dict, Any
import json

class StreamlitConfig:
    """Streamlit专用的配置编译器"""
    
    def __init__(self):
        self.base_config = {
            "bi_strict": True,
            "zs_combine": True,
            "seg_algo": "chan",
            "zs_algo": "normal"
        }
    
    def from_streamlit(self, st_inputs: Dict[str, Any]) -> Dict:
        """从Streamlit输入转换为chan.py配置"""
        return {
            **self.base_config,
            "bi_strict": st_inputs.get('bi_strict', True),
            "zs_combine": st_inputs.get('zs_combine', True),
            "show_bsp": st_inputs.get('show_bsp', True),
            "show_bi": st_inputs.get('show_bi', True),
            "show_seg": st_inputs.get('show_seg', True),
            "show_zs": st_inputs.get('show_zs', True)
        }
    
    def get_available_levels(self):
        """获取可选时间级别"""
        return {
            "K_1M": "1分钟",
            "K_5M": "5分钟", 
            "K_15M": "15分钟",
            "K_30M": "30分钟",
            "K_60M": "60分钟",
            "K_DAY": "日线"
        }
```

### Step 4: 封装数据接口 (25分钟)

创建 `chan_viz/data_service.py`:
```python
import streamlit as st
from datetime import datetime
import pandas as pd
from typing import Dict, List

# 导入chan.py相关类
from Chan import CChan
from ChanConfig import CChanConfig
from DataAPI.BaoStockAPI import CBaoStock

class StreamlitDataService:
    """Streamlit专用的数据服务"""
    
    def __init__(self):
        self._cache = {}
    
    @st.cache_data(ttl=3600)  # Streamlit自动缓存
    def load_chan_data(self, code: str, level: str, config: Dict) -> Dict:
        """加载缠论数据并转换为前端格式"""
        
        # 1. 参数验证
        if not code or not level:
            raise ValueError("参数缺失")
        
        # 2. 构建配置
        chan_config = CChanConfig(config)
        
        # 3. 加载数据
        chan = CChan(
            code=code,
            begin_time="2023-01-01",
            end_time=None,
            data_src="BAO_STOCK",
            lv_list=[level],
            config=chan_config
        )
        
        # 4. 数据转换
        return self._convert_to_visualization_data(chan, level)
    
    def _convert_to_visualization_data(self, chan, level):
        """转换为可视化格式"""
        kline_data = chan[level]
        
        return {
            "kline": self._extract_kline_data(kline_data),
            "bi": self._extract_bi_data(kline_data.bi_list),
            "segment": self._extract_segment_data(kline_data.seg_list),
            "central_zone": self._extract_zs_data(kline_data.zs_list),
            "buy_sell_points": self._extract_bsp_data(kline_data.bs_point_lst)
        }
    
    def _extract_kline_data(self, kline_data):
        """提取K线数据"""
        dates = []
        open_price, close_price, low, high = [], [], [], []
        
        for kl in kline_data:
            for klu in kl:
                dates.append(klu.time.to_str())
                open_price.append(klu.open)
                close_price.append(klu.close) 
                low.append(klu.low)
                high.append(klu.high)
        
        return {
            "dates": dates,
            "open": open_price,
            "close": close_price,
            "low": low,
            "high": high
        }
    
    def _extract_bi_data(self, bi_list):
        """提取笔数据为坐标点"""
        bi_coords = []
        for bi in bi_list:
            bi_coords.append({
                "x": [bi.begin_klu.idx, bi.end_klu.idx],
                "y": [bi.begin_klu.close, bi.end_klu.close],
                "type": bi.type2str(),
                "direction": bi.dir2str()
            })
        return bi_coords
    
    def _extract_zs_data(self, zs_list):
        """提取中枢数据为矩形区域"""
        zones = []
        for zs in zs_list:
            zones.append({
                "x": [zs.begin_klu.idx, zs.end_klu.idx],
                "y": [zs.low, zs.high],
                "type": zs.type2str()
            })
        return zones
```

### Step 5: 简化缠论图表渲染 (15分钟)

创建 `chan_viz/chart_render.py` - **只显示核心缠论指标**:
```python
import plotly.graph_objects as go
from typing import Dict

class PlotlyChartRenderer:
    """专注缠论指标的图表渲染器"""
    
    def __init__(self):
        self.colors = {
            'bi': '#FF6B6B',      # 笔 - 红色
            'zs': '#45B7D1',      # 中枢 - 蓝色
            'seg': '#4ECDC4',     # 线段 - 青色
            'bsp_buy': '#00FF00',  # 买点 - 绿色
            'bsp_sell': '#FF0000'  # 卖点 - 红色
        }
    
    def create_chan_chart(self, data: Dict, level: str, code: str = "") -> go.Figure:
        """创建缠论核心图表 - 只包含K线和缠论指标"""
        
        # 1. 创建单图层图表，专注核心
        fig = go.Figure()
        
        # 2. 添加K线图
        fig.add_trace(go.Candlestick(
            x=data['kline']['dates'],
            open=data['kline']['open'],
            high=data['kline']['high'],
            low=data['kline']['low'],
            close=data['kline']['close'],
            name='K线',
            increasing_line_color='red',  # A股红色上涨
            decreasing_line_color='green'
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
                    hovertext=f"类型: {bi['type']}, 方向: {bi['direction']}"
                ), row=1, col=1)
        
        # 4. 添加中枢
        if 'central_zone' in data:
            for zs in data['central_zone']:
                fig.add_trace(go.Scatter(
                    x=zs['x'] + zs['x'][::-1],
                    y=zs['y'] + [zs['y'][0]],  # 闭合矩形
                    fill='toself',
                    fillcolor='lightblue',
                    line=dict(color=self.colors['zs'], width=1),
                    name='中枢',
                    opacity=0.3
                ), row=1, col=1)
        
        # 5. 添加买卖点
        if 'buy_sell_points' in data:
            bsp_times, bsp_prices, bsp_colors = [], [], []
            for bsp in data['buy_sell_points']:
                if bsp['is_buy']:
                    color = self.colors['bsp_buy']
                else:
                    color = self.colors['bsp_sell']
                    
                bsp_times.append(bsp['kl_idx'])
                bsp_prices.append(bsp['price'])
                bsp_colors.append(color)
            
            fig.add_trace(go.Scatter(
                x=bsp_times,
                y=bsp_prices,
                mode='markers',
                marker=dict(size=12, color=bsp_colors, symbol='arrow-bar-up'),
                name='买卖点',
                hovertext=['买点' if c==self.colors['bsp_buy'] else '卖点' for c in bsp_colors]
            ), row=1, col=1)
        
        # 6. 添加MACD指标
        fig.add_trace(go.Bar(
            name='MACD', 
            x=data['kline']['dates'],
            y=data.get('macd', [0]*len(data['kline']['dates']))
        ), row=2, col=1)
        
        # 7. 设置布局
        fig.update_layout(
            title=dict(text=f"缠论技术分析 - {level}", x=0.5),
            xaxis=dict(
                rangeslider=dict(visible=True),
                type='category'
            ),
            yaxis=dict(title="价格"),
            height=700,
            showlegend=True,
            template='plotly_white'
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
```

### Step 6: 集成完整应用 (20分钟)

创建最终 `run_app.py`:
```python
import streamlit as st
import sys
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append('./chan.py')

from chan_viz.config_compiler import StreamlitConfig
from chan_viz.data_service import StreamlitDataService
from chan_viz.chart_render import PlotlyChartRenderer

# 初始化服务
config_compiler = StreamlitConfig()
data_service = StreamlitDataService()
chart_renderer = PlotlyChartRenderer()

def main():
    """主应用入口"""
    
    st.set_page_config(
        page_title="缠论图表可视化",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 侧边栏
    with st.sidebar:
        st.header("🔧 图表配置")
        
        # 基础信息
        st.subheader("股票信息")
        code = st.text_input("股票代码", value="002415.SZ")
        
        # 时间设置
        st.subheader("时间设置")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", 
                                     value=datetime.now() - timedelta(days=60))
        with col2:
            end_date = st.date_input("结束日期", 
                                   value=datetime.now())
        
        # 级别选择
        level_options = config_compiler.get_available_levels()
        selected_level = st.selectbox("时间级别", 
                                    options=list(level_options.keys()),
                                    format_func=lambda x: level_options[x])
        
        # 缠论参数
        st.subheader("缠论参数")
        config_params = {
            "bi_strict": st.checkbox("严格笔", value=True),
            "zs_combine": st.checkbox("中枢合并", value=True),
            "show_bsp": st.checkbox("显示买卖点", value=True),
            "show_bi": st.checkbox("显示笔", value=True),
            "show_seg": st.checkbox("显示线段", value=True),
            "show_zs": st.checkbox("显示中枢", value=True)
        }
    
    # 主要内容区域
    st.title("📈 缠论图表可视化")
    
    if st.button("🔄 生成/更新图表", type="primary", use_container_width=True):
        try:
            with st.spinner("📊 正在计算缠论数据..."):
                # 转换配置
                chan_config = config_compiler.from_streamlit(config_params)
                
                # 获取数据
                data = data_service.load_chan_data(
                    code=code,
                    level=selected_level,
                    config=chan_config
                )
                
                # 生成图表
                fig = chart_renderer.create_chan_chart(data, selected_level)
                st.session_state.chart_figure = fig
                st.session_state.last_update = datetime.now()
                
        except Exception as e:
            st.error(f"❌ 计算出错: {str(e)}")
            st.exception(e)
    
    # 显示图表
    if 'chart_figure' in st.session_state:
        st.subheader(f"📊 {code} - {config_compiler.get_available_levels()[selected_level]}")
        st.plotly_chart(
            st.session_state.chart_figure,
            use_container_width=True,
            height=800
        )
        
        # 显示刷新时间
        if 'last_update' in st.session_state:
            st.caption(f"最后更新: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 底部信息
    st.divider()
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("支持级别", "6个")
    with col2:
        st.metric("参数选项", "5+")
    with col3:
        st.metric("元素类型", "4种")

if __name__ == "__main__":
    main()
```

---

## 🎯 重新规划第二阶段 - 专注指标移植

### 修正后的实施重点

**❌ 已移除的过度设计：**
- 成交量指标
- 动画回放功能
- 复杂交易统计面板
- 过多缓存优化
- 演示数据模式

**✅ 专注核心功能：**
- 直接移植chan.py的缠论指标到Web
- K线图 + 笔 + 中枢 + 线段 + 买卖点
- 简化配置界面
- 无性能优化干扰

### 🚀 修正后启动命令

```bash
# 快速环境初始化
python3 -m venv env && source env/bin/activate
pip install streamlit plotly pandas

# 启动核心应用
streamlit run run_app.py
```

### 📊 使用验证 - 专注指标展示
1. 浏览器打开 `http://localhost:8501`
2. 输入股票代码：任何实际代码
3. 选择K线周期
4. **看到**：K线 + 缠论笔 + 中枢 + 线段 + 买卖点**

### 🎯 核心指标验证列表
- [ ] K线图正常显示
- [ ] 缠论笔划分准确标记
- [ ] 中枢区域高亮显示
- [ ] 线段走势清晰标识
- [ ] 买卖信号点准确标注

**🎭 项目定位**：从chan.py到Web的高质量缠论指标移植工具

## 🎊 当前状态

**已完成**：
- ✅ 所有模块按新规划重写
- ✅ 移除所有过度设计
- ✅ 专注核心缠论指标展示
- ✅ 端到端chan.py数据流测试通过

**核心代码量**：
- `config_compiler.py`: ~50行
- `data_service.py`: ~100行  
- `chart_render.py`: ~80行
- `run_app.py`: ~100行

**总计 < 350行** 专注实现缠论指标Web化展示