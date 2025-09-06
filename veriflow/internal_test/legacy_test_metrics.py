#!/usr/bin/env python3
"""
UVM Lite Metrics 功能测试脚本

测试新增的MRED、NMED、SNR、PSNR计算功能以及增强的match功能
"""

import numpy as np
import logging
from veriflow import (
    MetricsCalculator, 
    DataMatcher,
    calculate_mred,
    calculate_nmed,
    calculate_snr,
    calculate_psnr,
    match_data,
    analyze_error_metrics,
    print_separator
)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def test_basic_metrics():
    """测试基本指标计算功能"""
    print_separator("测试基本指标计算功能")
    
    # 创建测试数据
    np.random.seed(42)
    reference = np.random.randn(100) * 10 + 5
    noise = np.random.randn(100) * 0.1
    test = reference + noise
    
    print(f"参考信号: 均值={np.mean(reference):.3f}, 标准差={np.std(reference):.3f}")
    print(f"测试信号: 均值={np.mean(test):.3f}, 标准差={np.std(test):.3f}")
    
    # 使用便捷函数计算指标
    mred_val = calculate_mred(reference, test)
    nmed_val = calculate_nmed(reference, test)
    snr_val = calculate_snr(reference, test)
    psnr_val = calculate_psnr(reference, test)
    
    print(f"MRED: {mred_val:.6e}")
    print(f"NMED: {nmed_val:.6e}")
    print(f"SNR: {snr_val:.2f} dB")
    print(f"PSNR: {psnr_val:.2f} dB")
    
    # 验证结果合理性
    assert mred_val > 0, "MRED应该大于0"
    assert nmed_val > 0, "NMED应该大于0"
    assert snr_val > 0, "SNR应该大于0"
    assert psnr_val > 0, "PSNR应该大于0"
    
    print("✅ 基本指标计算测试通过")


def test_data_matching():
    """测试数据匹配功能"""
    print_separator("测试数据匹配功能")
    
    # 创建测试数据
    reference = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    test = np.array([1, 2, 3, 4, 5.1, 6, 7, 8, 9, 10.5])  # 有两个不匹配
    
    print(f"参考数据: {reference}")
    print(f"测试数据: {test}")
    
    # 使用便捷函数进行匹配
    match_result = match_data(reference, test, tolerance=0.2, max_mismatches=5)
    
    print(f"匹配结果:")
    print(f"  总元素数: {match_result['total_elements']}")
    print(f"  匹配数: {match_result['match_count']}")
    print(f"  不匹配数: {match_result['mismatch_count']}")
    print(f"  匹配率: {match_result['match_percentage']:.2f}%")
    print(f"  是否完全匹配: {match_result['is_match']}")
    
    # 验证结果
    assert match_result['total_elements'] == 10, "总元素数应该是10"
    assert match_result['mismatch_count'] == 2, "应该有2个不匹配"
    assert not match_result['is_match'], "不应该完全匹配"
    
    print("✅ 数据匹配测试通过")


def test_error_analysis():
    """测试误差分析功能"""
    print_separator("测试误差分析功能")
    
    # 创建测试数据
    np.random.seed(123)
    reference = np.random.randn(200) * 5 + 10
    noise_level = 0.5
    noise = np.random.randn(200) * noise_level
    test = reference + noise
    
    print(f"参考信号: 均值={np.mean(reference):.3f}, 标准差={np.std(reference):.3f}")
    print(f"噪声水平: {noise_level}")
    print(f"测试信号: 均值={np.mean(test):.3f}, 标准差={np.std(test):.3f}")
    
    # 使用误差分析函数
    analysis_result = analyze_error_metrics(
        reference, 
        test, 
        max_value=np.max(np.abs(reference)),
        tolerance=1e-10
    )
    
    print(f"误差分析结果:")
    summary = analysis_result['summary']
    print(f"  信噪比: {summary['snr_db']:.2f} dB")
    print(f"  峰值信噪比: {summary['psnr_db']:.2f} dB")
    print(f"  最大相对误差: {summary['mred']:.6e}")
    print(f"  归一化平均误差: {summary['nmed']:.6e}")
    print(f"  平均绝对误差: {summary['mean_error']:.6e}")
    print(f"  最大绝对误差: {summary['max_error']:.6e}")
    
    # 验证结果
    assert summary['snr_db'] > 0, "SNR应该大于0"
    assert summary['psnr_db'] > 0, "PSNR应该大于0"
    assert summary['mred'] > 0, "MRED应该大于0"
    assert summary['nmed'] > 0, "NMED应该大于0"
    assert summary['mean_error'] > 0, "平均绝对误差应该大于0"
    assert summary['max_error'] > 0, "最大绝对误差应该大于0"
    
    print("✅ 误差分析测试通过")


def test_multidimensional_data():
    """测试多维数据处理"""
    print_separator("测试多维数据处理")
    
    # 创建2D测试数据
    reference_2d = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    test_2d = np.array([[1, 2, 3], [4, 5.1, 6], [7, 8, 9.2]])  # 有两个不匹配
    
    print("参考数据 (2D):")
    print(reference_2d)
    print("\n测试数据 (2D):")
    print(test_2d)
    
    # 计算指标
    calc = MetricsCalculator()
    metrics_2d = calc.calculate_all_metrics(reference_2d, test_2d)
    
    # 进行匹配
    matcher = DataMatcher(tolerance=0.2, max_mismatches=10)
    match_result_2d = matcher.match(reference_2d, test_2d)
    
    print(f"2D数据处理结果:")
    print(f"  MRED: {metrics_2d['mred']:.6e}")
    print(f"  SNR: {metrics_2d['snr']:.2f} dB")
    print(f"  匹配率: {match_result_2d['match_percentage']:.2f}%")
    
    # 验证结果
    assert metrics_2d['mred'] > 0, "MRED应该大于0"
    assert metrics_2d['snr'] > 0, "SNR应该大于0"
    assert match_result_2d['mismatch_count'] == 2, "应该有2个不匹配"
    
    print("✅ 多维数据处理测试通过")


def test_error_handling():
    """测试错误处理"""
    print_separator("测试错误处理")
    
    calc = MetricsCalculator()
    
    try:
        # 测试形状不匹配
        reference = np.array([1, 2, 3])
        test = np.array([1, 2])
        calc.mred(reference, test)
        assert False, "应该抛出ValueError"
    except ValueError as e:
        print(f"✅ 捕获到预期的错误: {e}")
    
    try:
        # 测试空数组
        reference = np.array([])
        test = np.array([])
        calc.mred(reference, test)
        assert False, "应该抛出ValueError"
    except ValueError as e:
        print(f"✅ 捕获到预期的错误: {e}")
    
    print("✅ 错误处理测试通过")


def main():
    """主函数"""
    print_separator("UVM Lite Metrics 功能测试")
    print("测试新增的MRED、NMED、SNR、PSNR计算功能以及增强的match功能")
    
    try:
        # 运行各个测试
        test_basic_metrics()
        test_data_matching()
        test_error_analysis()
        test_multidimensional_data()
        test_error_handling()
        
        print_separator("测试完成")
        print("🎉 所有测试通过！")
        
    except Exception as e:
        print_separator("测试失败")
        print(f"❌ 测试失败: {e}")
        raise


if __name__ == "__main__":
    main() 