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
        # 只传递chan.py实际支持的参数
        return {
            **self.base_config,
            "bi_strict": st_inputs.get('bi_strict', True),
            "zs_combine": st_inputs.get('zs_combine', True)
            # show_* 参数用于前端显示控制，不传给chan.py
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