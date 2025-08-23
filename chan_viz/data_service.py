import streamlit as st
from datetime import datetime
from typing import Dict
import sys

# 导入chan.py相关类
try:
    sys.path.append('../chan.py')
    from Chan import CChan
    from ChanConfig import CChanConfig
    CHAN_AVAILABLE = True
except ImportError as e:
    CHAN_AVAILABLE = False

# 定义核心数据函数，修复缓存问题
@st.cache_data(ttl=3600)
def load_chan_data(code: str, level: str, config: Dict, start_date: str = None, end_date: str = None) -> Dict:
    """加载缠论数据并转换为前端格式"""
    
    # 参数验证
    if not code or not level:
        raise ValueError("参数缺失")
    
    # 设置默认日期范围
    if not start_date:
        start_date = "2023-01-01"
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 构建配置
    chan_config = CChanConfig(config) if CHAN_AVAILABLE else type('_Config', (), {})()
    
    try:
        if CHAN_AVAILABLE:
            # 加载真实数据
            chan = CChan(
                code=code,
                begin_time=start_date,
                end_time=end_date,
                data_src="BAO_STOCK",
                lv_list=[level],
                config=chan_config
            )
            return _convert_to_visualization_data(chan, level)
        else:
            # 使用模拟数据
            return _get_mock_data()
            
    except Exception as e:
        print(f"数据加载错误: {e}")
        return _get_mock_data()

@st.cache_data(ttl=3600)
def _convert_to_visualization_data(chan, level):
    """转换为可视化格式"""
    try:
        kline_data = chan[level]
        return {
            "kline": _extract_kline_data(kline_data),
            "bi": _extract_bi_data(getattr(kline_data, 'bi_list', [])),
            "segment": _extract_segment_data(getattr(kline_data, 'seg_list', [])),
            "central_zone": _extract_zs_data(getattr(kline_data, 'zs_list', [])),
            "buy_sell_points": _extract_bsp_data(getattr(kline_data, 'bs_point_lst', []))
        }
    except:
        return _get_mock_data()

@st.cache_data(ttl=3600)
def _extract_kline_data(kline_data):
    """提取K线数据"""
    dates = []
    open_price, close_price, low, high = [], [], [], []
    
    try:
        for kl in kline_data:
            for klu in kl:
                dates.append(str(klu.time))
                open_price.append(float(klu.open))
                close_price.append(float(klu.close))
                low.append(float(klu.low))
                high.append(float(klu.high))
    except:
        # 模拟数据
        import random
        from datetime import datetime, timedelta
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(20)]
        dates.reverse()
        base_price = 100
        
        for i in range(20):
            open_p = base_price + random.uniform(-3, 3)
            close_p = open_p + random.uniform(-2, 2)
            high_p = max(open_p, close_p) + random.uniform(0, 1.5)
            low_p = min(open_p, close_p) - random.uniform(0, 1.5)
            
            open_price.append(round(open_p, 2))
            close_price.append(round(close_p, 2))
            low.append(round(low_p, 2))
            high.append(round(high_p, 2))
            base_price = close_p
    
    return {
        "dates": dates,
        "open": open_price,
        "close": close_price,
        "low": low,
        "high": high
    }

@st.cache_data(ttl=3600)
def _extract_bi_data(bi_list):
    """提取笔数据"""
    bi_coords = []
    try:
        for bi in bi_list:
            bi_coords.append({
                "x": [int(bi.begin_klu.idx), int(bi.end_klu.idx)],
                "y": [float(bi.begin_klu.close), float(bi.end_klu.close)],
                "type": str(getattr(bi, 'type', '笔')),
                "direction": "up" if getattr(bi, 'dir', 1) > 0 else "down"
            })
    except:
        # 模拟数据
        bi_coords = [
            {"x": [0, 5], "y": [100, 105], "type": "上升笔", "direction": "up"},
            {"x": [5, 10], "y": [105, 98], "type": "下降笔", "direction": "down"}
        ]
    return bi_coords

@st.cache_data(ttl=3600)
def _extract_zs_data(zs_list):
    """提取中枢数据"""
    zones = []
    try:
        for zs in zs_list:
            zones.append({
                "x": [int(zs.begin_klu.idx), int(zs.end_klu.idx)],
                "y": [float(zs.low), float(zs.high)],
                "type": str(getattr(zs, 'type', '中枢'))
            })
    except:
        # 模拟数据
        zones = [
            {"x": [3, 8], "y": [98, 102], "type": "中枢"}
        ]
    return zones

@st.cache_data(ttl=3600)
def _extract_segment_data(seg_list):
    """提取线段数据"""
    segments = []
    try:
        for seg in seg_list:
            segments.append({
                "x": [int(seg.begin_klu.idx), int(seg.end_klu.idx)],
                "y": [float(seg.begin_klu.close), float(seg.end_klu.close)],
                "type": str(getattr(seg, 'type', '线段'))
            })
    except:
        segments = []
    return segments

@st.cache_data(ttl=3600)
def _extract_bsp_data(bsp_list):
    """提取买卖点数据"""
    bsp_data = []
    try:
        for bsp in bsp_list:
            bsp_data.append({
                "kl_idx": int(bsp.klu.idx),
                "price": float(bsp.klu.close),
                "is_buy": bool(bsp.is_buy),
                "type": str(getattr(bsp, 'type', '买卖点'))
            })
    except:
        # 模拟数据
        bsp_data = [
            {"kl_idx": 12, "price": 103, "is_buy": True, "type": "买点"},
            {"kl_idx": 18, "price": 98, "is_buy": False, "type": "卖点"}
        ]
    return bsp_data

@st.cache_data(ttl=3600)
def _get_mock_data():
    """获取模拟数据"""
    import random
    from datetime import datetime, timedelta
    
    # 生成模拟K线数据
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(15)]
    dates.reverse()
    base_price = 100
    open_price, close_price, low, high = [], [], [], []
    
    for i in range(15):
        open_p = base_price + random.uniform(-2, 2)
        close_p = open_p + random.uniform(-1.5, 1.5)
        high_p = max(open_p, close_p) + random.uniform(0, 1)
        low_p = min(open_p, close_p) - random.uniform(0, 1)
        
        open_price.append(round(open_p, 2))
        close_price.append(round(close_p, 2))
        low.append(round(low_p, 2))
        high.append(round(high_p, 2))
        base_price = close_p
    
    return {
        "kline": {
            "dates": dates,
            "open": open_price,
            "close": close_price,
            "low": low,
            "high": high
        },
        "bi": [
            {"x": [0, 3], "y": [100, 102], "type": "上升笔", "direction": "up"},
            {"x": [3, 7], "y": [102, 98], "type": "下降笔", "direction": "down"},
            {"x": [7, 12], "y": [98, 101], "type": "上升笔", "direction": "up"}
        ],
        "central_zone": [
            {"x": [4, 8], "y": [99, 101], "type": "中枢"}
        ],
        "segment": [
            {"x": [0, 12], "y": [100, 101], "type": "线段"}
        ],
        "buy_sell_points": [
            {"kl_idx": 12, "price": 101, "is_buy": True, "type": "买点"},
            {"kl_idx": 14, "price": 100.5, "is_buy": False, "type": "卖点"}
        ]
    }

class StreamlitDataService:
    """数据服务包装，保持接口兼容"""
    def __init__(self):
        pass
    
    def load_chan_data(self, code: str, level: str, config: Dict, start_date: str = None, end_date: str = None) -> Dict:
        """调用全局缓存函数"""
        return load_chan_data(code, level, config, start_date, end_date)