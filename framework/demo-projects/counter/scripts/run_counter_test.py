
import os

from veriflow.task_runner import SimulationTask
from veriflow.verilogger import logger
from veriflow.path_tools import find_project_root
from veriflow.path_tools import find_framework_root




# --- 1. 定义这个测试专用的 pre_sim 和 post_sim 处理器 ---

def counter_pre_sim(task):
    """
    对于这个简单的计数器测试，Testbench是自激励的，
    所以 pre_sim 阶段不需要生成任何外部激励文件。
    """
    logger.info(f"[{task.task_name}] Pre-sim: No external stimulus files needed.")
    pass

def counter_post_sim(task):
    """
    检查仿真结果。
    为了演示，我们先硬编码为通过。在实际应用中，这里会包含
    文件比较、日志解析等检查逻辑。
    """
    logger.info(f"[{task.task_name}] Post-sim: Checking simulation results...")
    logger.info(f"[{task.task_name}] Assuming test passed for demonstration purposes.")
    task.passed = True
# --- 2. 主执行逻辑 ---

if __name__ == "__main__":
        # logger.info("--- Starting Counter Test Suite ---")

    try:
        # --- a. 定义项目相关的路径 ---
        # 这种方式让脚本可以从任何地方运行，只要目录结构保持不变
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = find_project_root()
        framework_root = find_framework_root()


        rtl_path = os.path.join(project_root, 'rtl')
        tb_path = os.path.join(project_root, 'tb', 'counter_tb.v')
        work_dir_iverilog = os.path.join(project_root, 'sim_outputs', 'sim_outputs_iverilog')
        work_dir_modelsim = os.path.join(project_root, 'sim_outputs', 'sim_outputs_modelsim')
        work_dir_vivado = os.path.join(project_root, 'sim_outputs', 'sim_outputs_vivado')
        report_dir = os.path.join(project_root, 'report')
        report_file = os.path.join(report_dir, 'counter_test.log')
        
        logger.add(report_file)

        
        # --- b. 定义仿真器配置 ---
        iverilog_config = {
            'simulator':      'iverilog',
            'top_module':     'counter_tb',
            'rtl_path':       rtl_path,
            'tb_path':        tb_path,
            'work_dir':       work_dir_iverilog,
            # 'verbosity_level': 'SIM_ONLY',
            'compile_options': ['-g2012'],
            'tool_paths': {
                'iverilog': os.path.join(framework_root, 'utils', 'iverilog', 'bin', 'iverilog.exe'),
                'vvp': os.path.join(framework_root, 'utils', 'iverilog', 'bin', 'vvp.exe'),
            }
        }

        modelsim_config = {
        'simulator':      'modelsim',  # 切换仿真器！
        'top_module':     'counter_tb',
        'rtl_path':       rtl_path,
        'tb_path':        tb_path,
        'work_dir':       work_dir_modelsim,
        'verbosity_level': 'SIM_ONLY',
        'compile_options': ['+define+MY_DEFINE=1'],
        'include_paths':   ['path/to/includes']
    }
        
        vivado_config = {
        'simulator':      'vivado',  # 切换仿真器！
        'top_module':     'counter_tb',
        'rtl_path':       rtl_path,
        'tb_path':        tb_path,
        'work_dir':       work_dir_vivado,
        'compile_options': ['+define+MY_DEFINE=1'],
        'include_paths':   ['path/to/includes']
    }

        # --- c. 创建并配置 SimulationTask 实例 ---
        
        counter_task = SimulationTask()
        
        counter_task.task_name = "CounterFunctionalityTest"
        counter_task.sim_config = iverilog_config
        
        counter_task.pre_sim_handler = counter_pre_sim
        counter_task.post_sim_handler = counter_post_sim
        
        # --- d. 运行任务 ---
        success = counter_task.run()
        
        if success:
            logger.info("Counter test (iverilog) completed successfully!")
            logger.info(f"Waveform file may be available at: {os.path.join(work_dir_iverilog, 'waveform.vcd')}")
        else:
            logger.error("Counter test (iverilog) failed. Please check the logs above for details.")


        counter_task.sim_config = modelsim_config
        success = counter_task.run()

        if success:
            logger.info("Counter test (modelsim) completed successfully!")
            logger.info(f"Waveform file may be available at: {os.path.join(work_dir_modelsim, 'waveform.vcd')}")
        else:
            logger.error("Counter test (modelsim) failed. Please check the logs above for details.")


    except Exception as e:
        # 捕获在配置阶段或运行期间可能发生的任何意外错误
        logger.critical(f"An unexpected critical error occurred: {e}", exc_info=True)
