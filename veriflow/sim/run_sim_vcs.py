# -----------------------------------------------------------------------------
# file: veriflow/sim/run_sim_vcs.py
#
# Synopsys VCS 仿真器的具体实现。
# 定义了 run_vcs 函数，它会被 SimulationTask 动态加载和调用。
# 流程包括：编译、连接、仿真。
#
# v1.0 更新:
# - 实现了完整的VCS仿真流程
# - 添加了宏定义支持
# v2.0 更新:
# - 使用VeriLogger统一日志接口
# -----------------------------------------------------------------------------

import os

# 从同一包内的 simulators 模块导入工具函数
from .simulators import execute_command, find_rtl_files, format_macro_defines
# 导入统一的verilogger
from ..verilogger import logger as verilogger


def run_vcs(top_module, rtl_path, tb_path, work_dir, 
            task_name=None, compile_options=None, sim_options=None, 
            include_paths=None, tool_paths=None, defines=None):
    """
    使用 Synopsys VCS 运行仿真。
    这是被 SimulationTask 调用的核心流程函数。
    
    :param top_module: 顶层模块名称
    :param rtl_path: RTL源文件路径
    :param tb_path: 测试平台文件路径
    :param work_dir: 工作目录
    :param task_name: 任务名称（可选）
    :param compile_options: 编译选项列表（可选）
    :param sim_options: 仿真选项列表（可选）
    :param include_paths: 包含路径列表（可选）
    :param tool_paths: 工具路径字典（可选）
    :param defines: 宏定义字典（可选），格式为 {'MACRO_NAME': 'value', 'MACRO_NAME2': None}
    """
    verilogger.subtitle(f"Preparing VCS Simulation for task: {task_name}")

    # 初始化可选参数
    compile_options = compile_options or []
    sim_options = sim_options or []
    include_paths = include_paths or []
    tool_paths = tool_paths or {}
    macro_defines = defines or {}  # 为了内部代码清晰，使用macro_defines变量名

    # 从 tool_paths 获取工具路径，如果不存在，则假设它们在系统PATH中
    vcs_exe = tool_paths.get('vcs', 'vcs')

    rtl_files_list = find_rtl_files(rtl_path)
    all_files_to_compile = rtl_files_list + [os.path.abspath(tb_path)]

    # --- 编译和连接步骤 ---
    verilogger.subtitle("[VCS] Starting Compilation and Linking")
    
    # 构建 VCS 命令
    compile_cmd_parts = [
        f'"{vcs_exe}"',
        '-sverilog',        # 启用 SystemVerilog 支持
        '-debug_access+all', # 启用完全调试访问
        '-kdb',             # 启用知识数据库以支持调试
        '-lca',             # 启用 Line Coverage Analysis
        '-timescale=1ns/1ps', # 设置时间单位
        f'-o "{os.path.join(work_dir, "simv")}"',  # 指定可执行文件输出路径
    ]

    # 添加 include 路径 (VCS 使用 +incdir+<path>)
    for path in include_paths:
        compile_cmd_parts.append(f'+incdir+"{os.path.abspath(path)}"')

    # 添加宏定义
    if macro_defines:
        verilogger.info(f"Processing {len(macro_defines)} macro definitions")
        macro_args = format_macro_defines(macro_defines, 'vcs')
        compile_cmd_parts.extend(macro_args)

    # 添加自定义编译选项
    compile_cmd_parts.extend(compile_options)

    # 添加所有待编译文件
    for file_path in all_files_to_compile:
        compile_cmd_parts.append(f'"{file_path}"')

    compile_cmd = ' '.join(compile_cmd_parts)
    
    # 在 work_dir 中执行编译
    execute_command(compile_cmd, work_dir=work_dir)
    verilogger.success("[VCS] Compilation and Linking Successful")

    # --- 仿真步骤 ---
    verilogger.subtitle("[VCS] Starting Simulation")
    
    # 构建仿真命令
    simulate_cmd_parts = [
        os.path.join(work_dir, 'simv'),  # 使用生成的可执行文件
        '-l sim.log',        # 指定日志文件
        '+vcs+dumpvars+waveform.vpd',  # 生成波形文件
    ]
    
    # 添加自定义仿真选项
    simulate_cmd_parts.extend(sim_options)

    simulate_cmd = ' '.join(simulate_cmd_parts)
    
    # 在 work_dir 中执行仿真
    execute_command(simulate_cmd, work_dir=work_dir)
    verilogger.success("[VCS] Simulation Successful")

    # 检查波形文件是否存在
    wave_file_path = os.path.join(work_dir, "waveform.vpd")
    if os.path.exists(wave_file_path):
        verilogger.info(f"Waveform file generated: {wave_file_path}")
    else:
        verilogger.warning("Waveform file 'waveform.vpd' not found. Check your simulation settings.")

    # 检查日志文件是否存在
    log_file_path = os.path.join(work_dir, "sim.log")
    if os.path.exists(log_file_path):
        verilogger.info(f"Simulation log file generated: {log_file_path}")
    else:
        verilogger.warning("Simulation log file 'sim.log' not found.")
