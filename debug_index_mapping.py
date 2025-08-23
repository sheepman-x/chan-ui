#!/usr/bin/env python3
"""
缠论指标位置调试脚本

用于排查笔、线段等缠论指标在图表上位置偏移的问题
分析K线索引与缠论对象索引的映射关系
"""

import sys
import os
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
chan_path = os.path.join(project_root, 'chan.py')
sys.path.append(chan_path)

try:
    from Chan import CChan
    from ChanConfig import CChanConfig
    from Common.CEnum import DATA_SRC, KL_TYPE, BI_DIR
    from chan_viz.data_service import StreamlitDataService
    CHAN_AVAILABLE = True
except ImportError as e:
    print(f"Warning: chan.py not available: {e}")
    CHAN_AVAILABLE = False

def debug_index_mapping():
    """调试索引映射关系"""
    if not CHAN_AVAILABLE:
        print("chan.py framework not available")
        return
    
    print("=" * 80)
    print("🔍 缠论指标位置调试分析")
    print("=" * 80)
    
    # 测试参数
    test_code = "sz.000001"
    test_config = {
        "bi_strict": True,
        "zs_combine": True,
        "bs_type": "1,2,3a,3b"
    }
    start_date = "2023-06-01"
    end_date = "2023-12-31"
    
    print(f"📊 测试股票: {test_code}")
    print(f"📅 时间范围: {start_date} ~ {end_date}")
    print()
    
    # 1. 获取chan.py原始数据
    print("🔄 获取chan.py原始数据...")
    chan_config = CChanConfig(test_config)
    chan = CChan(
        code=test_code,
        begin_time=start_date,
        end_time=end_date,
        data_src=DATA_SRC.BAO_STOCK,
        lv_list=[KL_TYPE.K_DAY],
        config=chan_config
    )
    
    kline_list = chan.kl_datas[KL_TYPE.K_DAY]
    print(f"✅ 成功获取数据")
    print(f"📈 合并K线数量: {len(kline_list)}")
    print(f"📍 笔数量: {len(kline_list.bi_list)}")
    print(f"📏 线段数量: {len(kline_list.seg_list)}")
    print(f"🏛️ 中枢数量: {len(kline_list.zs_list)}")
    print()
    
    # 2. 分析K线单元结构
    print("🔍 分析K线单元结构...")
    total_klu_count = 0
    klu_to_date_mapping = {}  # K线单元索引 -> 日期
    date_to_klu_mapping = {}  # 日期 -> K线单元索引
    klc_to_klu_range = {}     # 合并K线索引 -> K线单元范围
    
    for klc_idx, klc in enumerate(kline_list):
        start_klu_idx = total_klu_count
        klc_klu_count = len(klc.lst)
        
        for klu_local_idx, klu in enumerate(klc.lst):
            klu_global_idx = total_klu_count + klu_local_idx
            date_str = str(klu.time)
            
            klu_to_date_mapping[klu_global_idx] = date_str
            date_to_klu_mapping[date_str] = klu_global_idx
        
        klc_to_klu_range[klc_idx] = (start_klu_idx, start_klu_idx + klc_klu_count - 1)
        total_klu_count += klc_klu_count
    
    print(f"📊 总K线单元数: {total_klu_count}")
    print(f"🗓️ 日期范围: {min(klu_to_date_mapping.values())} ~ {max(klu_to_date_mapping.values())}")
    print()
    
    # 3. 分析笔的索引映射
    print("📍 分析笔的索引映射...")
    for i, bi in enumerate(kline_list.bi_list[:5]):  # 只显示前5个笔
        print(f"\n--- 笔 {i+1} ---")
        print(f"开始合并K线: klc[{bi.begin_klc.idx}]")
        print(f"结束合并K线: klc[{bi.end_klc.idx}]")
        
        # 获取对应的K线单元范围
        begin_klu_range = klc_to_klu_range.get(bi.begin_klc.idx, "未找到")
        end_klu_range = klc_to_klu_range.get(bi.end_klc.idx, "未找到")
        
        print(f"开始K线单元范围: {begin_klu_range}")
        print(f"结束K线单元范围: {end_klu_range}")
        
        # 获取实际价格和日期
        if bi.dir == BI_DIR.UP:
            start_price = float(bi.begin_klc.low)
            end_price = float(bi.end_klc.high)
            start_date_actual = str(bi.begin_klc.lst[0].time)  # 第一个K线单元的时间
            end_date_actual = str(bi.end_klc.lst[-1].time)     # 最后一个K线单元的时间
        else:
            start_price = float(bi.begin_klc.high)
            end_price = float(bi.end_klc.low)
            start_date_actual = str(bi.begin_klc.lst[0].time)
            end_date_actual = str(bi.end_klc.lst[-1].time)
        
        print(f"实际日期: {start_date_actual} ~ {end_date_actual}")
        print(f"实际价格: {start_price:.2f} ~ {end_price:.2f}")
        print(f"方向: {'上升' if bi.dir == BI_DIR.UP else '下降'}")
    
    print("\n" + "=" * 80)
    
    # 4. 获取转换后的数据进行对比
    print("🔄 获取数据转换结果...")
    data_service = StreamlitDataService()
    converted_data = data_service.load_chan_data(
        code=test_code,
        level="K_DAY",
        config=test_config,
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"📈 转换后K线数量: {len(converted_data['kline']['dates'])}")
    print(f"📍 转换后笔数量: {len(converted_data['bi'])}")
    print()
    
    # 5. 对比分析索引映射问题
    print("🔍 对比分析索引映射问题...")
    dates = converted_data['kline']['dates']
    
    for i, (bi_original, bi_converted) in enumerate(zip(kline_list.bi_list[:3], converted_data['bi'][:3])):
        print(f"\n--- 笔 {i+1} 对比分析 ---")
        
        # 原始数据
        print(f"【原始】合并K线索引: {bi_original.begin_klc.idx} -> {bi_original.end_klc.idx}")
        start_date_orig = str(bi_original.begin_klc.lst[0].time)
        end_date_orig = str(bi_original.end_klc.lst[-1].time)
        print(f"【原始】实际日期: {start_date_orig} -> {end_date_orig}")
        
        # 转换后数据
        converted_start_idx, converted_end_idx = bi_converted['x']
        print(f"【转换】K线单元索引: {converted_start_idx} -> {converted_end_idx}")
        
        if converted_start_idx < len(dates) and converted_end_idx < len(dates):
            converted_start_date = dates[converted_start_idx]
            converted_end_date = dates[converted_end_idx]
            print(f"【转换】对应日期: {converted_start_date} -> {converted_end_date}")
            
            # 检查日期是否匹配
            start_match = start_date_orig == converted_start_date
            end_match = end_date_orig == converted_end_date
            print(f"【匹配】起点日期: {'✅' if start_match else '❌'} | 终点日期: {'✅' if end_match else '❌'}")
            
            if not start_match:
                print(f"【差异】起点 - 原始: {start_date_orig} vs 转换: {converted_start_date}")
            if not end_match:
                print(f"【差异】终点 - 原始: {end_date_orig} vs 转换: {converted_end_date}")
        else:
            print("【错误】索引超出范围!")
    
    # 6. 分析可能的原因
    print("\n" + "=" * 80)
    print("🎯 问题分析总结")
    print("=" * 80)
    
    print("可能的原因分析：")
    print("1. 合并K线索引 vs K线单元索引混淆")
    print("2. 索引映射时使用了错误的基准")
    print("3. 时间序列对齐问题")
    print("4. 数据提取逻辑错误")
    
    # 7. 详细的K线结构分析
    print("\n📋 详细K线结构分析（前10个合并K线）：")
    for i in range(min(10, len(kline_list))):
        klc = kline_list[i]
        klu_range = klc_to_klu_range[i]
        first_date = str(klc.lst[0].time)
        last_date = str(klc.lst[-1].time)
        klu_count = len(klc.lst)
        
        print(f"klc[{i:2d}]: K线单元范围[{klu_range[0]:3d}-{klu_range[1]:3d}], "
              f"包含{klu_count}个K线单元, 日期 {first_date} ~ {last_date}")

def main():
    debug_index_mapping()

if __name__ == "__main__":
    main()