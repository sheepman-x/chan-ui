import streamlit as st
from datetime import datetime
import pandas as pd
from typing import Dict, List
import sys

# 导入chan.py相关类
try:
    sys.path.append('../chan.py')
    from Chan import CChan
    from ChanConfig import CChanConfig
    from DataAPI.BaoStockAPI import CBaoStock
    CHAN_AVAILABLE = True
except ImportError as e:
    print(f"Import warning: {e}")
    # 创建模拟数据类用于开发测试
    class CChan:
        def __init__(self, **kwargs):
            pass
        def __getitem__(self, level):
            return MockKlineData()
    
    class CChanConfig:
        def __init__(self, config):
            pass
    
    class CBaoStock:
        pass
    CHAN_AVAILABLE = False

class MockKlineData:
    """模拟K线数据类用于开发测试"""
    def __init__(self):
        self.bi_list = []
        self.seg_list = []
        self.zs_list = []
        self.bs_point_lst = []

class StreamlitDataService:
    """Streamlit专用的数据服务"""
    
    def __init__(self):
        self._cache = {}
    
    @st.cache_data(ttl=3600)  # Streamlit自动缓存
    def load_chan_data(self, code: str, level: str, config: Dict, start_date: str = None, end_date: str = None) -> Dict:
        """加载缠论数据并转换为前端格式"""
        
        # 1. 参数验证
        if not code or not level:
            raise ValueError("参数缺失")
        
        # 2. 构建配置
        chan_config = CChanConfig(config)
        
        # 3. 设置默认日期范围
        if not start_date:
            start_date = "2023-01-01"
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # 4. 加载数据
            chan = CChan(
                code=code,
                begin_time=start_date,
                end_time=end_date,
                data_src="BAO_STOCK",
                lv_list=[level],
                config=chan_config
            )
            
            # 5. 数据转换
            return self._convert_to_visualization_data(chan, level)
            
        except Exception as e:
            # 开发模式使用模拟数据
            return self._get_mock_data()
    
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
        
        try:
            for kl in kline_data:
                for klu in kl:
                    dates.append(str(klu.time))
                    open_price.append(klu.open)
                    close_price.append(klu.close) 
                    low.append(klu.low)
                    high.append(klu.high)
        except:
            # 模拟数据
            import random
            from datetime import datetime, timedelta
            dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
            base_price = 100
            for i in range(30):
                open_p = base_price + random.uniform(-5, 5)
                close_p = open_p + random.uniform(-3, 3)
                high_p = max(open_p, close_p) + random.uniform(0, 2)
                low_p = min(open_p, close_p) - random.uniform(0, 2)
                open_price.append(open_p)
                close_price.append(close_p)
                low.append(low_p)
                high.append(high_p)
        
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
        try:
            for bi in bi_list:
                bi_coords.append({
                    "x": [bi.begin_klu.idx, bi.end_klu.idx],
                    "y": [bi.begin_klu.close, bi.end_klu.close],
                    "type": str(bi.type) if hasattr(bi, 'type') else "未知",
                    "direction": "up" if hasattr(bi, 'dir') and bi.dir > 0 else "down"
                })
        except:
            # 模拟数据
            bi_coords = [
                {"x": [0, 5], "y": [100, 105], "type": "上升笔", "direction": "up"},
                {"x": [5, 10], "y": [105, 98], "type": "下降笔", "direction": "down"},
                {"x": [10, 15], "y": [98, 102], "type": "上升笔", "direction": "up"}
            ]
        return bi_coords
    
    def _extract_zs_data(self, zs_list):
        """提取中枢数据为矩形区域"""
        zones = []
        try:
            for zs in zs_list:
                zones.append({
                    "x": [zs.begin_klu.idx, zs.end_klu.idx],
                    "y": [zs.low, zs.high],
                    "type": str(zs.type) if hasattr(zs, 'type') else "中枢"
                })
        except:
            # 模拟数据
            zones = [
                {"x": [5, 10], "y": [99, 101], "type": "中枢"}
            ]
        return zones
    
    def _extract_segment_data(self, seg_list):
        """提取线段数据"""
        segments = []
        try:
            for seg in seg_list:
                segments.append({
                    "x": [seg.begin_klu.idx, seg.end_klu.idx],
                    "y": [seg.begin_klu.close, seg.end_klu.close],
                    "type": str(seg.type) if hasattr(seg, 'type') else "线段"
                })
        except:
            segments = []
        return segments
    
    def _extract_bsp_data(self, bsp_list):
        """提取买卖点数据"""
        bsp_data = []
        try:
            for bsp in bsp_list:
                bsp_data.append({
                    "kl_idx": bsp.klu.idx,
                    "price": bsp.klu.close,
                    "is_buy": bsp.is_buy,
                    "type": str(bsp.type) if hasattr(bsp, 'type') else "买卖点"
                })
        except:
            # 模拟数据
            bsp_data = [
                {"kl_idx": 15, "price": 102, "is_buy": True, "type": "买点"},
                {"kl_idx": 25, "price": 108, "is_buy": False, "type": "卖点"}
            ]
        return bsp_data
    
    def _get_mock_data(self):
        """获取模拟数据用于开发测试"""
        import random
        from datetime import datetime, timedelta
        
        # 生成模拟K线数据
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
        base_price = 100
        open_price, close_price, low, high = [], [], [], []
        
        for i in range(30):
            open_p = base_price + random.uniform(-5, 5)
            close_p = open_p + random.uniform(-3, 3)
            high_p = max(open_p, close_p) + random.uniform(0, 2)
            low_p = min(open_p, close_p) - random.uniform(0, 2)
            open_price.append(open_p)
            close_price.append(close_p)
            low.append(low_p)
            high.append(high_p)
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
                {"x": [0, 5], "y": [100, 105], "type": "上升笔", "direction": "up"},
                {"x": [5, 10], "y": [105, 98], "type": "下降笔", "direction": "down"},
                {"x": [10, 15], "y": [98, 102], "type": "上升笔", "direction": "up"}
            ],
            "central_zone": [
                {"x": [5, 10], "y": [99, 101], "type": "中枢"}
            ],
            "segment": [
                {"x": [0, 15], "y": [100, 102], "type": "线段"}
            ],
            "buy_sell_points": [
                {"kl_idx": 15, "price": 102, "is_buy": True, "type": "买点"},
                {"kl_idx": 25, "price": 108, "is_buy": False, "type": "卖点"}
            ]
        }