"""
VeriFlow: A comprehensive Python-based digital circuit verification and simulation framework.

This package provides:
- Digital circuit simulation with multiple simulator support
- Verilog-style bit vector operations with strong typing
- Signal processing metrics calculation (MRED, NMED, SNR, PSNR)
- Memory file processing tools
- Automated task management and reporting
"""

# 导出主要类和函数
from .task_runner import SimulationTask
from .verilogger import logger

# 导出新的指标计算功能
from .verilog_bits import VerilogBits
from .metrics import (
    MetricsCalculator,
    DataMatcher,
    calculate_mred,
    calculate_nmed,
    calculate_snr,
    calculate_psnr,
    match_data,
    analyze_error_metrics
)

# 导出内存文件处理工具
from .mem_tools import (
    MemTools,
    read_memh,
    read_memb,
    write_memh,
    write_memb
)

# 导出路径工具
from .path_tools import (
    PathFinder,
    PathManager,
    find_framework_root,
    find_project_root,
    get_path_manager
)

__all__ = [
    'SimulationTask',
    'logger',
    'VerilogBits',
    'MetricsCalculator',
    'DataMatcher',
    'calculate_mred',
    'calculate_nmed',
    'calculate_snr',
    'calculate_psnr',
    'match_data',
    'analyze_error_metrics',
    'MemTools',
    'read_memh',
    'read_memb',
    'write_memh',
    'write_memb',
    'PathFinder',
    'PathManager',
    'find_framework_root',
    'find_project_root',
    'get_path_manager'
]
