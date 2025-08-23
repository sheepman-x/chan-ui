#!/usr/bin/env python3
"""
缠论数据转换单元测试

该测试文件验证从chan.py框架获取的真实数据与图表展示所需数据格式的转换逻辑是否正确。
测试覆盖：
1. K线数据提取和转换
2. 笔数据提取和坐标映射
3. 线段数据提取和坐标映射  
4. 中枢数据提取和坐标映射
5. 买卖点数据提取和坐标映射
6. 数据完整性和一致性验证
"""

import unittest
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

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

class TestChanDataConversion(unittest.TestCase):
    """缠论数据转换测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        if not CHAN_AVAILABLE:
            cls.skipTest(cls, "chan.py framework not available")
        
        cls.data_service = StreamlitDataService()
        
        # 测试股票代码和参数
        cls.test_code = "sz.000001"  # 平安银行
        cls.test_level = KL_TYPE.K_DAY
        cls.test_config = {
            "bi_strict": True,
            "zs_combine": True,
            "bs_type": "1,2,3a,3b"  # 使用chan.py支持的参数
        }
        cls.start_date = "2023-01-01"
        cls.end_date = "2024-01-01"
        
        print(f"Setting up test with code: {cls.test_code}, level: {cls.test_level}")
    
    def setUp(self):
        """每个测试方法前的初始化"""
        if not CHAN_AVAILABLE:
            self.skipTest("chan.py framework not available")
    
    def test_load_real_chan_data(self):
        """测试加载真实缠论数据"""
        print("\n=== 测试加载真实缠论数据 ===")
        
        try:
            # 创建CChan对象获取真实数据
            chan_config = CChanConfig(self.test_config)
            chan = CChan(
                code=self.test_code,
                begin_time=self.start_date,
                end_time=self.end_date,
                data_src=DATA_SRC.BAO_STOCK,
                lv_list=[self.test_level],
                config=chan_config
            )
            
            # 获取K线数据
            kline_list = chan.kl_datas[self.test_level]
            self.assertIsNotNone(kline_list, "K线数据不应为空")
            self.assertGreater(len(kline_list), 0, "K线数据应包含记录")
            
            print(f"✓ 成功加载K线数据，共 {len(kline_list)} 个合并K线")
            print(f"✓ 笔数量: {len(kline_list.bi_list)}")
            print(f"✓ 线段数量: {len(kline_list.seg_list)}")
            print(f"✓ 中枢数量: {len(kline_list.zs_list)}")
            print(f"✓ 买卖点数量: {len(kline_list.bs_point_lst.getSortedBspList())}")
            
            # 存储测试数据供其他测试方法使用
            self.__class__.chan_data = chan
            self.__class__.kline_list = kline_list
            
        except Exception as e:
            self.fail(f"加载真实缠论数据失败: {e}")
    
    def test_kline_data_conversion(self):
        """测试K线数据转换"""
        print("\n=== 测试K线数据转换 ===")
        
        if not hasattr(self.__class__, 'kline_list'):
            self.skipTest("需要先运行 test_load_real_chan_data")
        
        kline_list = self.__class__.kline_list
        converted_kline = self.data_service._extract_kline_data(kline_list)
        
        # 验证基础结构
        required_keys = ['dates', 'open', 'close', 'low', 'high', 'volume']
        for key in required_keys:
            self.assertIn(key, converted_kline, f"K线数据应包含 {key} 字段")
        
        # 验证数据长度一致性
        data_length = len(converted_kline['dates'])
        for key in required_keys:
            self.assertEqual(len(converted_kline[key]), data_length, 
                           f"所有K线字段长度应一致，{key}长度为{len(converted_kline[key])}")
        
        # 验证数据类型
        self.assertIsInstance(converted_kline['dates'][0], str, "日期应为字符串类型")
        self.assertIsInstance(converted_kline['open'][0], float, "开盘价应为浮点数")
        self.assertIsInstance(converted_kline['close'][0], float, "收盘价应为浮点数")
        
        # 验证价格合理性
        for i in range(data_length):
            self.assertGreaterEqual(converted_kline['high'][i], converted_kline['low'][i],
                                  f"第{i}个K线最高价应大于等于最低价")
            self.assertGreaterEqual(converted_kline['high'][i], converted_kline['open'][i],
                                  f"第{i}个K线最高价应大于等于开盘价")
            self.assertGreaterEqual(converted_kline['high'][i], converted_kline['close'][i],
                                  f"第{i}个K线最高价应大于等于收盘价")
        
        print(f"✓ K线数据转换成功，共{data_length}条记录")
        print(f"✓ 首个K线: 日期={converted_kline['dates'][0]}, 开盘={converted_kline['open'][0]:.2f}")
        print(f"✓ 末个K线: 日期={converted_kline['dates'][-1]}, 收盘={converted_kline['close'][-1]:.2f}")
    
    def test_bi_data_conversion(self):
        """测试笔数据转换和坐标验证"""
        print("\n=== 测试笔数据转换 ===")
        
        if not hasattr(self.__class__, 'kline_list'):
            self.skipTest("需要先运行 test_load_real_chan_data")
        
        kline_list = self.__class__.kline_list
        bi_list = kline_list.bi_list
        
        if len(bi_list) == 0:
            self.skipTest("当前数据没有笔，跳过笔数据转换测试")
        
        converted_bi = self.data_service._extract_bi_data(bi_list, self.data_service._build_klu_index_mapping(kline_list))
        
        # 验证基础结构
        self.assertIsInstance(converted_bi, list, "笔数据应为列表")
        self.assertGreater(len(converted_bi), 0, "应包含笔数据")
        
        total_klu_count = sum(len(klc.lst) for klc in kline_list)
        print(f"✓ K线单元总数: {total_klu_count}")
        
        for i, bi in enumerate(converted_bi):
            required_keys = ['x', 'y', 'type', 'direction']
            for key in required_keys:
                self.assertIn(key, bi, f"第{i}个笔应包含 {key} 字段")
            
            # 验证坐标数据
            self.assertIsInstance(bi['x'], list, "笔的x坐标应为列表")
            self.assertIsInstance(bi['y'], list, "笔的y坐标应为列表") 
            self.assertEqual(len(bi['x']), 2, "笔应有起点和终点x坐标")
            self.assertEqual(len(bi['y']), 2, "笔应有起点和终点y坐标")
            
            # 验证索引范围
            start_idx, end_idx = bi['x']
            self.assertGreaterEqual(start_idx, 0, f"第{i}个笔起始索引应≥0")
            self.assertLess(end_idx, total_klu_count, f"第{i}个笔结束索引应小于总K线数")
            self.assertLess(start_idx, end_idx, f"第{i}个笔起始索引应小于结束索引")
            
            # 验证价格数据
            start_price, end_price = bi['y']
            self.assertIsInstance(start_price, float, "笔起始价格应为浮点数")
            self.assertIsInstance(end_price, float, "笔结束价格应为浮点数")
            self.assertGreater(start_price, 0, "笔起始价格应大于0")
            self.assertGreater(end_price, 0, "笔结束价格应大于0")
            
            # 验证方向逻辑
            direction = bi['direction']
            self.assertIn(direction, ['up', 'down'], f"第{i}个笔方向应为up或down")
            
            if direction == 'up':
                self.assertLess(start_price, end_price, f"上升笔第{i}个起始价格应小于结束价格")
            else:  # down
                self.assertGreater(start_price, end_price, f"下降笔第{i}个起始价格应大于结束价格")
        
        print(f"✓ 笔数据转换成功，共{len(converted_bi)}个笔")
        for i, bi in enumerate(converted_bi[:3]):  # 显示前3个笔的信息
            print(f"  笔{i+1}: 索引{bi['x'][0]}->{bi['x'][1]}, "
                  f"价格{bi['y'][0]:.2f}->{bi['y'][1]:.2f}, 方向{bi['direction']}")
    
    def test_segment_data_conversion(self):
        """测试线段数据转换"""
        print("\n=== 测试线段数据转换 ===")
        
        if not hasattr(self.__class__, 'kline_list'):
            self.skipTest("需要先运行 test_load_real_chan_data")
        
        kline_list = self.__class__.kline_list
        seg_list = kline_list.seg_list
        
        if len(seg_list) == 0:
            self.skipTest("当前数据没有线段，跳过线段数据转换测试")
        
        converted_seg = self.data_service._extract_segment_data(seg_list, self.data_service._build_klu_index_mapping(kline_list))
        
        total_klu_count = sum(len(klc.lst) for klc in kline_list)
        
        for i, seg in enumerate(converted_seg):
            required_keys = ['x', 'y', 'type']
            for key in required_keys:
                self.assertIn(key, seg, f"第{i}个线段应包含 {key} 字段")
            
            # 验证坐标数据
            self.assertEqual(len(seg['x']), 2, "线段应有起点和终点x坐标")
            self.assertEqual(len(seg['y']), 2, "线段应有起点和终点y坐标")
            
            # 验证索引范围
            start_idx, end_idx = seg['x']
            self.assertGreaterEqual(start_idx, 0, f"第{i}个线段起始索引应≥0")
            self.assertLess(end_idx, total_klu_count, f"第{i}个线段结束索引应小于总K线数")
            self.assertLess(start_idx, end_idx, f"第{i}个线段起始索引应小于结束索引")
            
            # 验证价格数据  
            start_price, end_price = seg['y']
            self.assertGreater(start_price, 0, "线段起始价格应大于0")
            self.assertGreater(end_price, 0, "线段结束价格应大于0")
        
        print(f"✓ 线段数据转换成功，共{len(converted_seg)}个线段")
        for i, seg in enumerate(converted_seg[:3]):  # 显示前3个线段的信息
            print(f"  线段{i+1}: 索引{seg['x'][0]}->{seg['x'][1]}, "
                  f"价格{seg['y'][0]:.2f}->{seg['y'][1]:.2f}")
    
    def test_zs_data_conversion(self):
        """测试中枢数据转换"""
        print("\n=== 测试中枢数据转换 ===")
        
        if not hasattr(self.__class__, 'kline_list'):
            self.skipTest("需要先运行 test_load_real_chan_data")
        
        kline_list = self.__class__.kline_list
        zs_list = kline_list.zs_list
        
        if len(zs_list) == 0:
            self.skipTest("当前数据没有中枢，跳过中枢数据转换测试")
        
        converted_zs = self.data_service._extract_zs_data(zs_list, self.data_service._build_klu_index_mapping(kline_list))
        
        total_klu_count = sum(len(klc.lst) for klc in kline_list)
        
        for i, zs in enumerate(converted_zs):
            required_keys = ['x', 'y', 'type']
            for key in required_keys:
                self.assertIn(key, zs, f"第{i}个中枢应包含 {key} 字段")
            
            # 验证坐标数据
            self.assertEqual(len(zs['x']), 2, "中枢应有起点和终点x坐标")
            self.assertEqual(len(zs['y']), 2, "中枢应有低点和高点y坐标")
            
            # 验证索引范围
            start_idx, end_idx = zs['x']
            self.assertGreaterEqual(start_idx, 0, f"第{i}个中枢起始索引应≥0")
            self.assertLess(end_idx, total_klu_count, f"第{i}个中枢结束索引应小于总K线数")
            self.assertLessEqual(start_idx, end_idx, f"第{i}个中枢起始索引应小于等于结束索引")
            
            # 验证价格范围  
            low_price, high_price = zs['y']
            self.assertGreater(low_price, 0, "中枢低点价格应大于0")
            self.assertGreater(high_price, 0, "中枢高点价格应大于0")
            self.assertLessEqual(low_price, high_price, f"第{i}个中枢低点应小于等于高点")
        
        print(f"✓ 中枢数据转换成功，共{len(converted_zs)}个中枢")
        for i, zs in enumerate(converted_zs[:3]):  # 显示前3个中枢的信息
            print(f"  中枢{i+1}: 索引{zs['x'][0]}->{zs['x'][1]}, "
                  f"价格范围{zs['y'][0]:.2f}-{zs['y'][1]:.2f}")
    
    def test_bsp_data_conversion(self):
        """测试买卖点数据转换"""
        print("\n=== 测试买卖点数据转换 ===")
        
        if not hasattr(self.__class__, 'kline_list'):
            self.skipTest("需要先运行 test_load_real_chan_data")
        
        kline_list = self.__class__.kline_list
        bsp_list = kline_list.bs_point_lst
        
        if len(bsp_list.getSortedBspList()) == 0:
            self.skipTest("当前数据没有买卖点，跳过买卖点数据转换测试")
        
        converted_bsp = self.data_service._extract_bsp_data(bsp_list)
        
        total_klu_count = sum(len(klc.lst) for klc in kline_list)
        
        for i, bsp in enumerate(converted_bsp):
            required_keys = ['kl_idx', 'price', 'is_buy', 'type']
            for key in required_keys:
                self.assertIn(key, bsp, f"第{i}个买卖点应包含 {key} 字段")
            
            # 验证索引范围
            kl_idx = bsp['kl_idx']
            self.assertGreaterEqual(kl_idx, 0, f"第{i}个买卖点K线索引应≥0")
            self.assertLess(kl_idx, total_klu_count, f"第{i}个买卖点K线索引应小于总K线数")
            
            # 验证价格
            price = bsp['price']
            self.assertIsInstance(price, float, "买卖点价格应为浮点数")
            self.assertGreater(price, 0, "买卖点价格应大于0")
            
            # 验证买卖属性
            is_buy = bsp['is_buy']
            self.assertIsInstance(is_buy, bool, "is_buy应为布尔值")
            
            # 验证类型
            bsp_type = bsp['type']
            self.assertIsInstance(bsp_type, str, "买卖点类型应为字符串")
        
        buy_count = sum(1 for bsp in converted_bsp if bsp['is_buy'])
        sell_count = len(converted_bsp) - buy_count
        
        print(f"✓ 买卖点数据转换成功，共{len(converted_bsp)}个买卖点")
        print(f"  其中买点{buy_count}个，卖点{sell_count}个")
        
        for i, bsp in enumerate(converted_bsp[:3]):  # 显示前3个买卖点的信息
            label = "买点" if bsp['is_buy'] else "卖点"
            print(f"  {label}{i+1}: K线索引{bsp['kl_idx']}, 价格{bsp['price']:.2f}, 类型{bsp['type']}")
    
    def test_complete_data_conversion_integration(self):
        """测试完整数据转换集成"""
        print("\n=== 测试完整数据转换集成 ===")
        
        try:
            # 使用data_service的完整转换流程
            converted_data = self.data_service.load_chan_data(
                code=self.test_code,
                level="K_DAY",  # 使用字符串格式
                config=self.test_config,
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            # 验证顶级结构
            required_top_keys = ['kline', 'bi', 'segment', 'central_zone', 'buy_sell_points']
            for key in required_top_keys:
                self.assertIn(key, converted_data, f"转换后的数据应包含 {key}")
            
            # 验证K线数据结构
            kline_data = converted_data['kline']
            required_kline_keys = ['dates', 'open', 'close', 'low', 'high', 'volume']
            for key in required_kline_keys:
                self.assertIn(key, kline_data, f"K线数据应包含 {key}")
            
            # 验证数据一致性：所有时间相关的索引都应该在合理范围内
            dates_count = len(kline_data['dates'])
            
            # 验证笔的索引范围
            for bi in converted_data['bi']:
                for idx in bi['x']:
                    self.assertGreaterEqual(idx, 0, "笔索引应≥0")
                    self.assertLess(idx, dates_count, "笔索引应小于日期总数")
            
            # 验证线段的索引范围
            for seg in converted_data['segment']:
                for idx in seg['x']:
                    self.assertGreaterEqual(idx, 0, "线段索引应≥0")
                    self.assertLess(idx, dates_count, "线段索引应小于日期总数")
            
            # 验证中枢的索引范围
            for zs in converted_data['central_zone']:
                for idx in zs['x']:
                    self.assertGreaterEqual(idx, 0, "中枢索引应≥0")
                    self.assertLess(idx, dates_count, "中枢索引应小于日期总数")
            
            # 验证买卖点的索引范围
            for bsp in converted_data['buy_sell_points']:
                self.assertGreaterEqual(bsp['kl_idx'], 0, "买卖点索引应≥0")
                self.assertLess(bsp['kl_idx'], dates_count, "买卖点索引应小于日期总数")
            
            print("✓ 完整数据转换集成测试通过")
            print(f"  K线数据: {len(kline_data['dates'])} 条")
            print(f"  笔数据: {len(converted_data['bi'])} 个")  
            print(f"  线段数据: {len(converted_data['segment'])} 个")
            print(f"  中枢数据: {len(converted_data['central_zone'])} 个")
            print(f"  买卖点数据: {len(converted_data['buy_sell_points'])} 个")
            
            # 进行数据逻辑一致性检查
            self._validate_data_logic_consistency(converted_data)
            
        except Exception as e:
            self.fail(f"完整数据转换集成测试失败: {e}")
    
    def _validate_data_logic_consistency(self, data: Dict[str, Any]):
        """验证数据逻辑一致性"""
        print("\n--- 数据逻辑一致性验证 ---")
        
        # 验证笔的连续性：相邻笔的终点和起点应该连接
        bi_data = data['bi']
        if len(bi_data) > 1:
            for i in range(len(bi_data) - 1):
                current_end_idx = bi_data[i]['x'][1]
                next_start_idx = bi_data[i + 1]['x'][0] 
                # 注意：笔之间可能不是完全连续的，因为可能有合并K线
                self.assertLessEqual(current_end_idx, next_start_idx, 
                                   f"笔{i+1}的终点索引应≤笔{i+2}的起点索引")
        
        # 验证方向交替：相邻笔的方向应该相反
        if len(bi_data) > 1:
            for i in range(len(bi_data) - 1):
                current_direction = bi_data[i]['direction']
                next_direction = bi_data[i + 1]['direction']
                self.assertNotEqual(current_direction, next_direction,
                                  f"相邻笔{i+1}和{i+2}的方向应该相反")
        
        # 验证买卖点位置合理性：买卖点应该在K线索引范围内
        dates_count = len(data['kline']['dates'])
        for bsp in data['buy_sell_points']:
            kl_idx = bsp['kl_idx']
            self.assertGreaterEqual(kl_idx, 0, "买卖点索引应≥0")
            self.assertLess(kl_idx, dates_count, "买卖点索引应在K线范围内")
        
        print("✓ 数据逻辑一致性验证通过")


def run_tests():
    """运行测试的主函数"""
    print("=" * 60)
    print("🧪 缠论数据转换单元测试")
    print("=" * 60)
    
    # 创建测试套件，按照依赖顺序执行
    test_suite = unittest.TestSuite()
    test_class = TestChanDataConversion
    
    # 首先执行数据加载测试
    test_suite.addTest(test_class('test_load_real_chan_data'))
    
    # 然后执行各个组件的测试
    test_suite.addTest(test_class('test_kline_data_conversion'))
    test_suite.addTest(test_class('test_bi_data_conversion'))
    test_suite.addTest(test_class('test_segment_data_conversion'))
    test_suite.addTest(test_class('test_zs_data_conversion'))
    test_suite.addTest(test_class('test_bsp_data_conversion'))
    
    # 最后执行集成测试
    test_suite.addTest(test_class('test_complete_data_conversion_integration'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    print("\n" + "=" * 60)
    print("🏁 测试结果汇总")
    print("=" * 60)
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(f"跳过数: {len(result.skipped)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.skipped:
        print("\n⏭️ 跳过的测试:")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100 if result.testsRun > 0 else 0
    print(f"\n✅ 成功率: {success_rate:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)