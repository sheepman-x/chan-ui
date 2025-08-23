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