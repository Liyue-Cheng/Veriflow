# -----------------------------------------------------------------------------
# file: veriflow/task_runner.py
#
# 包含通用的仿真任务运行器 SimulationTask。
#
# 设计模式: "无状态、即时反应" (Stateless, Immediate-response)
#
# 这个最终版本的设计哲学是极致的简洁和直观。
# 对象的行为总是直接反映其当前的公共属性值，没有任何内部状态缓存或
# 复杂的生命周期管理。用户无需调用 reset()，任何配置更改都会立即生效。
# -----------------------------------------------------------------------------

import os
import inspect
import importlib
from typing import Optional, Dict, Callable, Any

# Import verilogger for unified output
from .verilogger import logger as verilogger



class SimulationTask:
    """
    一个"即时反应"的仿真任务运行器。
    它的行为总是直接反映其当前的公共属性值。
    """

    # --- 使用类属性注解来声明实例属性的类型 ---
    # task_name 可能是字符串，也可能在设置前是 None
    task_name: Optional[str]
    # sim_config 是一个字典
    sim_config: Dict[str, Any]
    # handler 是一个可调用对象(函数)，它接受一个 SimulationTask 实例作为参数，无返回值
    # 或者可以是 None
    pre_sim_handler: Optional[Callable[["SimulationTask"], None]]
    post_sim_handler: Optional[Callable[["SimulationTask"], None]]
    # passed 是一个布尔值
    passed: bool

    def __init__(self):
        """
        构造函数。只初始化用户需要配置的公共属性，并赋予安全的初始值。
        """
        self.task_name = None
        self.sim_config = {}
        self.pre_sim_handler = None
        self.post_sim_handler = None
        self.passed = False

    def _prepare_and_validate(self):
        """
        一个内部辅助方法，用于在每次需要时，基于当前属性进行校验和准备。
        v3.0 更新: work_dir 现在是必须由用户在 sim_config 中明确指定的参数。

        :return: (tuple) 一个包含 (simulator_name, run_config_dict) 的元组。
        """
        # verilogger.info(f"Preparing and validating config for task: '{self.task_name or 'Unnamed'}'...")

        # --- 基础校验 (不变) ---
        if not self.task_name or not isinstance(self.task_name, str):
            raise ValueError("Attribute 'task_name' must be set.")
        if not self.sim_config or not isinstance(self.sim_config, dict):
            raise ValueError("Attribute 'sim_config' must be set to a dictionary.")
        if "simulator" not in self.sim_config:
            raise ValueError("'simulator' key is required in 'sim_config'.")

        # --- ✨ 核心改动：强制检查 work_dir ✨ ---
        if "work_dir" not in self.sim_config or not self.sim_config["work_dir"]:
            raise ValueError(
                "The 'work_dir' key is a required and must be a non-empty path in 'sim_config'."
            )

        # 创建一个临时的、用于本次操作的配置副本
        run_config = self.sim_config.copy()
        simulator_name = run_config.pop("simulator").lower()

        # 自动注入 task_name
        run_config.setdefault("task_name", self.task_name)

        # ✨ 新的 work_dir 处理逻辑 ✨
        # 1. 获取用户必须提供的 work_dir
        work_dir = run_config["work_dir"]

        # 2. 确保它是一个绝对路径，以避免混淆
        #    如果用户提供了相对路径，我们会基于当前Python进程的工作目录将其转换为绝对路径
        if not os.path.isabs(work_dir):
            work_dir = os.path.abspath(work_dir)
            # 将规范化后的绝对路径更新回 run_config
            run_config["work_dir"] = work_dir
            verilogger.info(f"Relative work_dir converted to absolute path: {work_dir}")

        # 3. 确保物理目录存在于硬盘上
        os.makedirs(work_dir, exist_ok=True)

        # verilogger.info("Preparation and validation successful.")
        return simulator_name, run_config

    def pre_sim(self):
        """
        执行 pre-sim 阶段。
        """
        task_id = self.task_name or "Unnamed Task"
        # verilogger.title(f"Pre-Simulation Stage: {task_id}")
        self._prepare_and_validate()

        if self.pre_sim_handler is None:
            raise NotImplementedError(
                "'pre_sim_handler' attribute is not set for this task."
            )

        self.pre_sim_handler(self)
        # verilogger.info(f"Pre-simulation stage completed successfully")

    def run_sim(self):
        """
        执行 run-sim 阶段。
        """
        task_id = self.task_name or "Unnamed Task"
        verilogger.title(f"Simulation Stage: {task_id}")

        simulator_name, run_config = self._prepare_and_validate()

        # verilogger.info(f"Dispatching to '{simulator_name}' simulator...")
        try:
            module_name = f"veriflow.sim.run_sim_{simulator_name}"
            sim_module = importlib.import_module(module_name)
            runner_func = getattr(sim_module, f"run_{simulator_name}")
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Failed to load runner for '{simulator_name}': {e}"
            ) from e

        # 参数校验
        sig = inspect.signature(runner_func)
        supported_params = set(sig.parameters.keys())
        provided_params = set(run_config.keys())

        unsupported_params = provided_params - supported_params
        if unsupported_params:
            raise TypeError(
                f"Unsupported parameters for '{simulator_name}': {list(unsupported_params)}. "
                f"Supported are: {list(supported_params)}"
            )

        required_params = {
            p.name
            for p in sig.parameters.values()
            if p.default is inspect.Parameter.empty
        }
        missing_params = required_params - provided_params
        if missing_params:
            raise TypeError(
                f"Missing required parameters for '{simulator_name}': {list(missing_params)}"
            )

        # verilogger.info(f"Parameter validation for '{simulator_name}' passed.")
        runner_func(**run_config)
        verilogger.info(f"Simulation stage completed successfully")

    def post_sim(self):
        """
        执行 post-sim 阶段。
        :return: (bool) 返回任务的最终通过状态 (self.passed)。
        """
        task_id = self.task_name or "Unnamed Task"
        # verilogger.title(f"Post-Simulation Analysis: {task_id}")
        self._prepare_and_validate()

        if self.post_sim_handler is None:
            raise NotImplementedError(
                "'post_sim_handler' attribute is not set for this task."
            )

        self.passed = False  # 在检查前总是先重置结果状态
        self.post_sim_handler(self)

        # if self.passed:
        #     verilogger.info(f"Post-simulation analysis PASSED")
        # else:
        #     verilogger.error(f"Post-simulation analysis FAILED")
        return self.passed

    def run_full(self):
        """
        完整流程：执行完整的任务流程，按顺序调用 pre_sim, run_sim, post_sim。
        :return: (bool) 返回任务的最终通过状态 (self.passed)。
        """
        task_id = self.task_name or "Unnamed Task"
        verilogger.title(f"Starting Full Workflow: {task_id}")

        self.passed = False  # 每次完整运行时，重置最终结果

        try:
            self.pre_sim()
            self.run_sim()
            self.post_sim()
        except Exception as e:
            verilogger.error(f"Task '{task_id}' failed: {e}", exc_info=True)
            self.passed = False  # 确保任何异常都将最终结果置为失败

        # 打印最终结果
        if self.passed:
            verilogger.title(f"Task '{task_id}' PASSED (Full Workflow)")
            verilogger.info(f"✅ Task '{task_id}' completed successfully!")
        else:
            verilogger.title(f"Task '{task_id}' FAILED (Full Workflow)")
            verilogger.error(f"❌ Task '{task_id}' failed. Please check the logs above for details.")
        
        return self.passed

    def run_sim_only(self):
        """
        仅仿真：仅执行 run_sim 和 post_sim，跳过 pre_sim 阶段。
        适用于数据生成非常繁琐的情况，假设预处理数据已经准备好。
        :return: (bool) 返回任务的最终通过状态 (self.passed)。
        """
        task_id = self.task_name or "Unnamed Task"
        verilogger.title(f"Starting Simulation-Only Workflow: {task_id}")

        self.passed = False  # 每次运行时，重置最终结果

        try:
            verilogger.info("Skipping pre-simulation stage in sim-only mode...")
            self.run_sim()
            self.post_sim()
        except Exception as e:
            verilogger.error(f"Task '{task_id}' failed in sim-only mode: {e}", exc_info=True)
            self.passed = False  # 确保任何异常都将最终结果置为失败

        # 打印最终结果
        if self.passed:
            verilogger.title(f"Task '{task_id}' PASSED (Simulation-Only)")
            verilogger.info(f"✅ Task '{task_id}' completed successfully in sim-only mode!")
        else:
            verilogger.title(f"Task '{task_id}' FAILED (Simulation-Only)")
            verilogger.error(f"❌ Task '{task_id}' failed in sim-only mode. Please check the logs above for details.")
        
        return self.passed

    def run(self):
        """
        为了向后兼容性而保留的方法，等同于 run_full()。
        :return: (bool) 返回任务的最终通过状态 (self.passed)。
        """
        return self.run_full()
