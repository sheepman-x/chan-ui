import streamlit as st
from datetime import datetime
from typing import Dict
import sys
import os

# 兼容处理: 先检查Python版本，再尝试导入chan.py
try:
    import sys
    import subprocess
    
    # 检查Python版本
    if sys.version_info < (3, 11):
        CHAN_AVAILABLE = False
        CHAN_IMPORT_ERROR = f"Python版本过低，需要3.11+，当前为{sys.version_info.major}.{sys.version_info.minor}"
    else:
        chan_path = os.path.join(os.path.dirname(__file__), '..', 'chan.py')
        sys.path.insert(0, chan_path)  # 插入到开头确保优先加载
        
        # 检查chan.py目录是否为空（Streamlit Cloud submodule问题）
        if os.path.exists(chan_path) and os.path.isdir(chan_path):
            dir_contents = os.listdir(chan_path)
            if len(dir_contents) == 0:
                CHAN_AVAILABLE = False
                CHAN_IMPORT_ERROR = "chan.py目录为空，Streamlit Cloud未拉取submodule"
                print("⚠️ chan.py目录为空，使用模拟数据模式")
            else:
                from Chan import CChan
                from ChanConfig import CChanConfig
                CHAN_AVAILABLE = True
                CHAN_IMPORT_ERROR = None
        else:
            CHAN_AVAILABLE = False
            CHAN_IMPORT_ERROR = f"chan.py路径不存在: {chan_path}"
        
except Exception as e:
    CHAN_AVAILABLE = False
    CHAN_IMPORT_ERROR = str(e)

# 定义核心数据函数，修复缓存问题
@st.cache_data(ttl=3600)
def load_chan_data(code: str, level: str, config: Dict, start_date: str = None, end_date: str = None) -> Dict:
    """加载缠论数据并转换为前端格式"""
    
    # 参数验证
    if not code or not level:
        raise ValueError("参数缺失")
    
    # 转换股票代码格式：UI的.SZ/.SH格式 -> BaoStock的sz./sh.格式
    if code.endswith('.SZ'):
        baostock_code = f"sz.{code[:-3]}"
    elif code.endswith('.SH'):
        baostock_code = f"sh.{code[:-3]}"
    else:
        # 如果已经是BaoStock格式，直接使用
        baostock_code = code
    
    # 设置默认日期范围
    if not start_date:
        start_date = "2023-01-01"
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 确保chan.py可用
    if not CHAN_AVAILABLE:
        raise RuntimeError(f"chan.py不可用: {CHAN_IMPORT_ERROR}")
    
    # 构建配置
    chan_config = CChanConfig(config)
    
    try:
        # 加载真实数据
        chan = CChan(
            code=baostock_code,  # 使用转换后的代码格式
            begin_time=start_date,
            end_time=end_date,
            data_src="BAO_STOCK",
            lv_list=[level],
            config=chan_config
        )
        return _convert_to_visualization_data(chan, level)
            
    except Exception as e:
        print(f"数据加载错误: {e}")
        raise RuntimeError(f"无法获取股票数据，请检查股票代码和网络连接: {e}")

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
    open_price, close_price, low, high, volume = [], [], [], [], []
    
    try:
        for kl in kline_data:
            for klu in kl:
                dates.append(str(klu.time))
                open_price.append(float(klu.open))
                close_price.append(float(klu.close))
                low.append(float(klu.low))
                high.append(float(klu.high))
                volume.append(float(getattr(klu, 'volume', 0)))
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
            volume.append(random.randint(1000, 10000))
            base_price = close_p
    
    return {
        "dates": dates,
        "open": open_price,
        "close": close_price,
        "low": low,
        "high": high,
        "volume": volume
    }

@st.cache_data(ttl=3600)
def _extract_bi_data(bi_list):
    """提取笔数据"""
    bi_coords = []
    try:
        for bi in bi_list:
            # 修复：使用begin_klc和end_klc的idx
            bi_coords.append({
                "x": [int(bi.begin_klc.idx), int(bi.end_klc.idx)],
                "y": [float(bi.begin_klc.close), float(bi.end_klc.close)],
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
            # 修复：使用正确的中枢属性
            zones.append({
                "x": [int(zs.begin.idx), int(zs.end.idx)],
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
            # 修复：使用正确的线段属性
            segments.append({
                "x": [int(seg.begin_klc.idx), int(seg.end_klc.idx)],
                "y": [float(seg.begin_klc.close), float(seg.end_klc.close)],
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
                "price": float(bsp.bi.get_end_val()),
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
    """Streamlit专用的缠论数据服务"""
    
    def __init__(self):
        self.chan_available = CHAN_AVAILABLE
        self.chan_error = CHAN_IMPORT_ERROR
        if not CHAN_AVAILABLE:
            print(f"⚠️ chan.py依赖不可用，将使用模拟数据: {CHAN_IMPORT_ERROR}")
    
    @st.cache_data(ttl=3600)
    def load_chan_data(_self, code: str, level: str, config: Dict, start_date: str = None, end_date: str = None) -> Dict:
        """加载缠论数据并转换为前端格式"""
        
        # 参数验证
        if not code or not level:
            raise ValueError("参数缺失")
        
        # 转换股票代码格式：UI的.SZ/.SH格式 -> BaoStock的sz./sh.格式
        if code.endswith('.SZ'):
            baostock_code = f"sz.{code[:-3]}"
        elif code.endswith('.SH'):
            baostock_code = f"sh.{code[:-3]}"
        else:
            # 如果已经是BaoStock格式，直接使用
            baostock_code = code
        
        # 设置默认日期范围
        if not start_date:
            start_date = "2023-01-01"
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # 如果chan.py不可用，返回模拟数据
        if not _self.chan_available:
            print(f"📊 使用模拟数据（chan.py不可用: {_self.chan_error}）")
            return _get_mock_data()
        
        # 导入枚举类型
        from Common.CEnum import DATA_SRC, KL_TYPE
        
        # 转换级别字符串为KL_TYPE枚举
        level_mapping = {
            "K_DAY": KL_TYPE.K_DAY,
            "K_60M": KL_TYPE.K_60M,
            "K_30M": KL_TYPE.K_30M,
            "K_15M": KL_TYPE.K_15M,
            "K_5M": KL_TYPE.K_5M,
            "K_1M": KL_TYPE.K_1M
        }
        
        kl_type = level_mapping.get(level, KL_TYPE.K_DAY)
        
        # 构建配置
        chan_config = CChanConfig(config)
        
        try:
            # 加载真实数据
            chan = CChan(
                code=baostock_code,  # 使用转换后的代码格式
                begin_time=start_date,
                end_time=end_date,
                data_src=DATA_SRC.BAO_STOCK,
                lv_list=[kl_type],
                config=chan_config
            )
            return _self._convert_to_visualization_data(chan, kl_type)
                
        except Exception as e:
            print(f"数据加载错误: {e}")
            raise RuntimeError(f"无法获取股票数据，请检查股票代码和网络连接: {e}")
    
    def _convert_to_visualization_data(self, chan, level):
        """转换为可视化格式"""
        try:
            # 获取对应级别的K线列表
            kline_list = chan.kl_datas[level]
            
            # 构建K线单元全局索引映射
            klu_global_index_map = self._build_klu_index_mapping(kline_list)
            
            return {
                "kline": self._extract_kline_data(kline_list),
                "bi": self._extract_bi_data(kline_list.bi_list, klu_global_index_map),
                "segment": self._extract_segment_data(kline_list.seg_list, klu_global_index_map),
                "central_zone": self._extract_zs_data(kline_list.zs_list, klu_global_index_map),
                "buy_sell_points": self._extract_bsp_data(kline_list.bs_point_lst)
            }
        except Exception as e:
            raise RuntimeError(f"数据转换失败: {e}")
    
    def _build_klu_index_mapping(self, kline_list):
        """构建K线单元全局索引映射
        
        返回: {klc_idx: (start_klu_idx, end_klu_idx)}
        """
        klu_global_index_map = {}
        total_klu_count = 0
        
        for klc_idx, klc in enumerate(kline_list):
            start_klu_idx = total_klu_count
            klc_klu_count = len(klc.lst)
            end_klu_idx = start_klu_idx + klc_klu_count - 1
            
            klu_global_index_map[klc_idx] = (start_klu_idx, end_klu_idx)
            total_klu_count += klc_klu_count
        
        return klu_global_index_map
    
    def _extract_kline_data(self, kline_list):
        """提取K线数据"""
        dates = []
        open_price, close_price, low, high, volume = [], [], [], [], []
        
        # 遍历K线合并单元
        for kline_combine in kline_list:
            # 遍历合并单元中的每个K线单元
            for klu in kline_combine.lst:
                dates.append(str(klu.time))
                open_price.append(float(klu.open))
                close_price.append(float(klu.close))
                low.append(float(klu.low))
                high.append(float(klu.high))
                volume.append(float(getattr(klu, 'volume', 0)))
        
        return {
            "dates": dates,
            "open": open_price,
            "close": close_price,
            "low": low,
            "high": high,
            "volume": volume
        }
    
    def _extract_bi_data(self, bi_list, klu_global_index_map):
        """提取笔数据 - 遵循chan.py官方实现"""
        bi_coords = []
        for bi in bi_list:
            # 使用chan.py官方方法获取笔的精确坐标和价格
            begin_klu = bi.get_begin_klu()  # 获取起点的具体K线单元
            end_klu = bi.get_end_klu()      # 获取终点的具体K线单元
            begin_val = bi.get_begin_val()  # 获取起点的精确价格
            end_val = bi.get_end_val()      # 获取终点的精确价格
            
            bi_coords.append({
                "x": [int(begin_klu.idx), int(end_klu.idx)],
                "y": [float(begin_val), float(end_val)],
                "type": str(getattr(bi, 'type', '笔')),
                "direction": "up" if bi.is_up() else "down",
                "is_sure": bi.is_sure  # 是否为确定的笔
            })
        return bi_coords
    
    def _extract_zs_data(self, zs_list, klu_global_index_map):
        """提取中枢数据 - 遵循chan.py官方实现"""
        zones = []
        for zs in zs_list:
            # zs.begin 和 zs.end 已经是 CKLine_Unit 对象，直接使用它们的 idx
            # 这些 idx 已经是全局的 KLine Unit 索引，不需要再映射
            begin_klu_idx = int(zs.begin.idx)
            end_klu_idx = int(zs.end.idx)
            
            zones.append({
                "x": [begin_klu_idx, end_klu_idx],
                "y": [float(zs.low), float(zs.high)],
                "type": str(getattr(zs, 'type', '中枢')),
                "is_sure": bool(getattr(zs, 'is_sure', True))  # 添加确定性标识
            })
        return zones
    
    def _extract_segment_data(self, seg_list, klu_global_index_map):
        """提取线段数据 - 遵循chan.py官方实现"""
        segments = []
        for seg in seg_list:
            # 使用chan.py官方方法获取线段的精确坐标和价格
            begin_klu = seg.get_begin_klu()  # 获取起点的具体K线单元
            end_klu = seg.get_end_klu()      # 获取终点的具体K线单元
            begin_val = seg.get_begin_val()  # 获取起点的精确价格
            end_val = seg.get_end_val()      # 获取终点的精确价格
            
            segments.append({
                "x": [int(begin_klu.idx), int(end_klu.idx)],
                "y": [float(begin_val), float(end_val)],
                "type": str(getattr(seg, 'type', '线段')),
                "direction": "up" if seg.dir == 1 else "down",  # 线段方向
                "is_sure": bool(getattr(seg, 'is_sure', True))  # 是否为确定的线段
            })
        return segments
    
    def _extract_bsp_data(self, bsp_list):
        """提取买卖点数据"""
        bsp_data = []
        # BSP列表是CBSPointList对象，使用getSortedBspList()方法获取排序后的买卖点列表
        try:
            bsp_sorted = bsp_list.getSortedBspList()
            for bsp in bsp_sorted:
                # CBS_Point对象有klu属性，这是从bi.get_end_klu()获得的CKLine_Unit对象
                # klu.idx是K线在整个序列中的索引，price是笔的结束价格
                bsp_data.append({
                    "kl_idx": int(bsp.klu.idx),  # K线索引
                    "price": float(bsp.bi.get_end_val()),  # 笔的结束价格
                    "is_buy": bool(bsp.is_buy),
                    "type": str(bsp.type2str())
                })
        except Exception as e:
            print(f"BSP提取错误: {e}")
            # 如果提取失败，返回空列表
            pass
        return bsp_data