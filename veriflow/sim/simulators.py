# -----------------------------------------------------------------------------
# file: veriflow/sim/simulators.py
#
# 这是一个仿真工具箱模块。
# 它提供了一系列被各个具体仿真器脚本共享的通用辅助函数。
#
# v2.0 更新:
# - execute_command: 增加了对Windows系统下GBK编码的支持，以解决
#   UnicodeDecodeError 问题。
# - execute_command: 增加了 errors='replace' 选项，增强解码的健壮性。
# 
# v3.0 更新:
# - 添加了 format_macro_defines 函数，用于支持宏定义功能
# v4.0 更新:
# - 使用VeriLogger统一日志接口
# -----------------------------------------------------------------------------

import os
import subprocess
import glob
import platform  # 导入platform模块以检测操作系统

# 导入统一的verilogger
from ..verilogger import logger as verilogger


def execute_command(command, work_dir=None, execution_mode='buffered', output_level='FULL'):
    """
    一个通用的命令执行辅助函数。
    支持两种模式：'buffered' (执行后处理) 和 'streaming' (实时输出)。

    :param command: 要执行的命令字符串。
    :param work_dir: (可选) 命令执行时的工作目录。
    :param execution_mode: 'buffered' 或 'streaming'。
    :param output_level: 'FULL' 或 'QUIET' (仅在 buffered 模式下有效)。
    """
    # --- 参数校验 ---
    if execution_mode == 'streaming' and output_level != 'FULL':
        verilogger.warning(
            f"In 'streaming' mode, output_level must be 'FULL'. "
            f"Ignoring output_level='{output_level}' and proceeding with full output."
        )
        output_level = 'FULL'

    verilogger.debug(f"Executing command (Mode: {execution_mode}): {command}")
    if work_dir:
        verilogger.debug(f"Working directory: {work_dir}")

    # --- 动态确定编码 ---
    default_encoding = 'gbk' if platform.system() == "Windows" else 'utf-8'
    verilogger.debug(f"Using encoding: '{default_encoding}' for subprocess output decoding.")

    # --- 模式选择 ---
    if execution_mode == 'streaming':
        return _execute_streaming(command, work_dir, default_encoding)
    else: # buffered
        return _execute_buffered(command, work_dir, default_encoding, output_level)

def _execute_streaming(command, work_dir, encoding):
    """以流式方式执行命令，实时打印输出。"""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # 将 stderr 重定向到 stdout
            text=True,
            encoding=encoding,
            errors='replace',
            cwd=work_dir,
            bufsize=1 # 行缓冲
        )

        # 实时读取输出
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                verilogger.writeln(line.strip())
            process.stdout.close()

        return_code = process.wait()

        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)

        verilogger.debug("Streaming command executed successfully.")

    except subprocess.CalledProcessError as e:
        verilogger.error(f"Streaming command FAILED with return code {e.returncode}!")
        verilogger.error(f"Command: {e.cmd}")
        raise
    except Exception as e:
        verilogger.error(f"An unexpected error occurred during streaming execution: {command}")
        verilogger.error(str(e), exc_info=True)
        raise

def _execute_buffered(command, work_dir, encoding, output_level):
    """以缓冲方式执行命令，执行完毕后处理输出。"""
    try:
        process = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding=encoding,
            errors='replace',
            cwd=work_dir
        )
        
        verilogger.debug("Buffered command executed successfully.")
        
        if output_level == 'FULL':
            if process.stdout:
                verilogger.info(f"STDOUT:\n---\n{process.stdout.strip()}\n---")
            if process.stderr:
                verilogger.warning(f"STDERR:\n---\n{process.stderr.strip()}\n---")

    except subprocess.CalledProcessError as e:
        verilogger.error(f"Buffered command FAILED with return code {e.returncode}!")
        verilogger.error(f"Command: {e.cmd}")
        if e.stdout:
            verilogger.error(f"STDOUT:\n---\n{e.stdout.strip()}\n---")
        if e.stderr:
            verilogger.error(f"STDERR:\n---\n{e.stderr.strip()}\n---")
        raise
    except Exception as e:
        verilogger.error(f"An unexpected error occurred during buffered execution: {command}")
        verilogger.error(str(e), exc_info=True)
        raise


def find_rtl_files(rtl_path):
    """
    一个辅助函数，用于递归地查找所有 .v 和 .sv 文件。

    :param rtl_path: RTL文件的根搜索路径。
    :return: 包含所有找到的RTL文件绝对路径的列表。
    """
    rtl_path_abs = os.path.abspath(rtl_path)
    if not os.path.isdir(rtl_path_abs):
        verilogger.warning(f"RTL path '{rtl_path_abs}' does not exist or is not a directory.")
        return []
    
    files = []
    # 使用 glob 模块的 recursive=True 功能，相当于 MATLAB 的 '**/...'
    for ext in ('**/*.v', '**/*.sv'):
        pattern = os.path.join(rtl_path_abs, ext)
        files.extend(glob.glob(pattern, recursive=True))

    verilogger.info(f"Found {len(files)} RTL file(s) in '{rtl_path_abs}'.")
    return files


def format_macro_defines(macro_defines, simulator_type):
    """
    将宏定义字典转换为指定仿真器的命令行参数格式。
    
    :param macro_defines: 宏定义字典，格式为 {'MACRO_NAME': 'value', 'MACRO_NAME2': None}
                         如果值为None，则表示只定义宏名而不赋值
    :param simulator_type: 仿真器类型，支持 'iverilog', 'modelsim', 'vcs', 'vivado'
    :return: 格式化后的宏定义参数列表
    """
    if not macro_defines:
        return []
    
    if not isinstance(macro_defines, dict):
        raise ValueError("macro_defines must be a dictionary")
    
    verilogger.info(f"Formatting {len(macro_defines)} macro definitions for {simulator_type}")
    
    formatted_defines = []
    
    for macro_name, macro_value in macro_defines.items():
        if not isinstance(macro_name, str) or not macro_name.strip():
            verilogger.warning(f"Invalid macro name: {macro_name}, skipping")
            continue
            
        # 根据不同的仿真器类型格式化宏定义
        if simulator_type.lower() == 'iverilog':
            # Icarus Verilog 使用 -D 参数
            if macro_value is None:
                formatted_defines.append(f'-D{macro_name}')
            else:
                formatted_defines.append(f'-D{macro_name}={macro_value}')
                
        elif simulator_type.lower() == 'modelsim':
            # ModelSim/QuestaSim 使用 +define+ 参数
            if macro_value is None:
                formatted_defines.append(f'+define+{macro_name}')
            else:
                formatted_defines.append(f'+define+{macro_name}={macro_value}')
                
        elif simulator_type.lower() == 'vcs':
            # VCS 使用 +define+ 参数
            if macro_value is None:
                formatted_defines.append(f'+define+{macro_name}')
            else:
                formatted_defines.append(f'+define+{macro_name}={macro_value}')
                
        elif simulator_type.lower() == 'vivado':
            # Vivado 使用 -d 参数
            if macro_value is None:
                formatted_defines.append(f'-d {macro_name}')
            else:
                formatted_defines.append(f'-d {macro_name}={macro_value}')
        else:
            raise ValueError(f"Unsupported simulator type: {simulator_type}")
    
    verilogger.info(f"Generated {len(formatted_defines)} macro define arguments")
    return formatted_defines
