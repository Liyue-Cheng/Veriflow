# -----------------------------------------------------------------------------
# file: veriflow/sim/run_sim_iverilog.py
#
# Icarus Verilog 仿真器的具体实现。
# 定义了 run_iverilog 函数，它会被 SimulationTask 动态加载和调用。
#
# v2.0 更新:
# - 添加了宏定义支持，现在可以通过 macro_defines 参数传递宏定义
# v3.0 更新:
# - 使用VeriLogger统一日志接口
# -----------------------------------------------------------------------------

import os

# 从同一包内的 simulators 模块导入工具函数
from .simulators import execute_command, find_rtl_files, format_macro_defines
# 导入统一的verilogger
from ..verilogger import logger as verilogger


def run_iverilog(top_module, rtl_path, tb_path, work_dir, 
                 task_name=None, compile_options=None, include_paths=None, 
                 tool_paths=None, defines=None):
    """
    使用 Icarus Verilog 运行仿真。
    这是被 SimulationTask 调用的核心流程函数。
    
    :param top_module: 顶层模块名称
    :param rtl_path: RTL源文件路径
    :param tb_path: 测试平台文件路径
    :param work_dir: 工作目录
    :param task_name: 任务名称（可选）
    :param compile_options: 编译选项列表（可选）
    :param include_paths: 包含路径列表（可选）
    :param tool_paths: 工具路径字典（可选）
    :param defines: 宏定义字典（可选），格式为 {'MACRO_NAME': 'value', 'MACRO_NAME2': None}
    """
    verilogger.subtitle(f"Preparing Icarus Verilog Simulation for task: {task_name}")
    
    # 初始化可选参数
    compile_options = compile_options or []
    include_paths = include_paths or []
    tool_paths = tool_paths or {}
    macro_defines = defines or {}  # 为了内部代码清晰，使用macro_defines变量名

    # 从 tool_paths 获取路径，如果不存在，则使用默认值（假设在PATH中）
    iverilog_exe = tool_paths.get('iverilog', 'iverilog')
    vvp_exe = tool_paths.get('vvp', 'vvp')

    rtl_files_list = find_rtl_files(rtl_path)

    # --- 编译步骤 ---
    verilogger.subtitle("[Icarus] Starting Compilation")
    output_vvp_file = os.path.join(work_dir, "simulation.vvp")

    # 使用列表构建命令，更安全
    compile_cmd_parts = [
        f'"{iverilog_exe}"',
        f'-o "{output_vvp_file}"',
        f'-s {top_module}',
    ]

    # 添加include路径
    for path in include_paths:
        compile_cmd_parts.append(f'-I "{os.path.abspath(path)}"')
    
    # 添加宏定义
    if macro_defines:
        verilogger.info(f"Processing {len(macro_defines)} macro definitions")
        macro_args = format_macro_defines(macro_defines, 'iverilog')
        compile_cmd_parts.extend(macro_args)
    
    # 添加其他编译选项
    compile_cmd_parts.extend(compile_options)

    # 添加待编译的文件
    all_files_to_compile = rtl_files_list + [os.path.abspath(tb_path)]
    for file_path in all_files_to_compile:
        compile_cmd_parts.append(f'"{file_path}"')

    compile_cmd = ' '.join(compile_cmd_parts)
    
    # 编译命令的工作目录可以是None，因为它使用了绝对路径
    execute_command(compile_cmd, work_dir=None)
    verilogger.success("[Icarus] Compilation Successful")

    # --- 仿真步骤 ---
    verilogger.subtitle("[Icarus] Starting Simulation")
    simulate_cmd = f'"{vvp_exe}" "{output_vvp_file}"'
    
    # 仿真时，必须在 work_dir 中执行，以确保波形等文件生成在正确位置
    execute_command(simulate_cmd, work_dir=work_dir)
    verilogger.success("[Icarus] Simulation Successful")
    
    wave_file_path = os.path.join(work_dir, "waveform.vcd")
    if os.path.exists(wave_file_path):
        verilogger.info(f"Waveform file generated: {wave_file_path}")
    else:
        verilogger.warning("Waveform file 'waveform.vcd' not found. Check $dumpfile settings.")