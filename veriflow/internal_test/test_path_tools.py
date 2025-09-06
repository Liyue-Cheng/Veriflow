#!/usr/bin/env python3
"""
VeriFlow路径工具测试模块

使用unittest框架进行测试，可被回归测试自动发现和运行。

测试策略：
1. 创建临时的project_test测试目录结构
2. 在不同的项目中创建测试脚本
3. 运行这些脚本，验证路径查找是否正确
4. 清理测试环境，确保不留痕迹

黄金标准：框架根目录应该是当前文件的上两级目录
"""

import os
import sys
import shutil
import subprocess
import unittest
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from veriflow.path_tools import PathFinder, PathManager


class TestPathToolsBasic(unittest.TestCase):
    """基础路径工具测试"""
    
    def test_direct_framework_root_finding(self):
        """测试直接框架根目录查找"""
        current_framework = PathFinder.find_framework_root()
        expected_framework = str(Path(__file__).parent.parent.parent.resolve())
        
        self.assertEqual(current_framework, expected_framework, 
                        f"框架根目录查找错误: 期望={expected_framework}, 实际={current_framework}")

    def test_path_manager_creation(self):
        """测试路径管理器创建"""
        path_manager = PathManager()
        self.assertIsNotNone(path_manager)
        
    def test_framework_root_property(self):
        """测试框架根目录属性"""
        path_manager = PathManager()
        framework_root = path_manager.framework_root
        expected_framework = str(Path(__file__).parent.parent.parent.resolve())
        self.assertEqual(framework_root, expected_framework)
        
    def test_standard_paths(self):
        """测试标准路径获取"""
        path_manager = PathManager()
        paths = path_manager.get_standard_paths()
        
        # 检查必要的路径键存在
        required_keys = [
            'framework_root', 'project_root', 'veriflow_core', 
            'projects_dir', 'simulator_dir'
        ]
        for key in required_keys:
            self.assertIn(key, paths)
            
    def test_path_validation(self):
        """测试路径验证功能"""
        path_manager = PathManager()
        validation = path_manager.validate_paths()
        
        # 框架根目录和veriflow核心应该存在
        self.assertTrue(validation.get('framework_root', False))
        self.assertTrue(validation.get('veriflow_core', False))


class TestPathToolsAdvanced(unittest.TestCase):
    """高级路径工具测试 - 项目结构测试"""
    
    def setUp(self):
        """测试前设置"""
        # 黄金标准：框架根目录是当前文件的上两级目录
        self.expected_framework_root = str(Path(__file__).parent.parent.parent.resolve())
        self.test_root = None
        self.test_results = []
    
    def tearDown(self):
        """测试后清理"""
        if self.test_root and os.path.exists(self.test_root):
            try:
                shutil.rmtree(self.test_root)
            except Exception:
                pass  # 忽略清理失败

    def test_project_structure_detection(self):
        """测试项目结构检测"""
        success = self._run_complete_project_test()
        self.assertTrue(success, "项目结构测试失败")

    def _run_complete_project_test(self) -> bool:
        """运行完整的项目测试流程"""
        try:
            # 1. 设置测试环境
            if not self._setup_test_environment():
                return False
            
            # 2. 运行测试
            success = self._run_all_project_tests()
            
            return success
            
        finally:
            # 3. 清理环境
            self._cleanup_test_environment()

    def _setup_test_environment(self) -> bool:
        """设置测试环境"""
        try:
            # 在框架根目录下创建project_test
            self.test_root = os.path.join(self.expected_framework_root, "project_test")
            
            # 如果已存在，先删除
            if os.path.exists(self.test_root):
                shutil.rmtree(self.test_root)
            
            # 创建测试目录结构
            test_structure = {
                "category1/project1": ["rtl", "tb"],
                "category1/project2": ["sim_outputs"],
                "category2/project3": ["rtl"],
                "standalone_project": ["tb"]
            }
            
            for project_path, dirs in test_structure.items():
                full_project_path = os.path.join(self.test_root, project_path)
                os.makedirs(full_project_path, exist_ok=True)
                
                # 创建项目目录
                for dir_name in dirs:
                    os.makedirs(os.path.join(full_project_path, dir_name), exist_ok=True)
                
                # 为project3创建标记文件
                if "project3" in project_path:
                    marker_file = os.path.join(full_project_path, ".veriflow-project")
                    with open(marker_file, 'w') as f:
                        f.write("# VeriFlow测试项目\n")
                
                # 创建测试脚本
                self._create_test_script(full_project_path, project_path)
            
            return True
            
        except Exception as e:
            print(f"测试环境创建失败: {e}")
            return False

    def _create_test_script(self, project_path: str, project_name: str):
        """在指定项目中创建测试脚本"""
        # 使用原始字符串和正确的路径分隔符处理
        project_path_safe = project_path.replace('\\', '/')
        script_content = f'''#!/usr/bin/env python3
"""
测试脚本 for {project_name}
运行在: {project_path_safe}
"""

import os
import sys
from pathlib import Path

# 添加veriflow到路径
veriflow_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(veriflow_root))

from veriflow.path_tools import find_framework_root, find_project_root, get_path_manager

def main():
    # 当前脚本所在目录应该是项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找框架根目录
    framework_root = find_framework_root()
    
    # 查找项目根目录
    project_root = find_project_root()
    
    # 输出结果（格式化为易于解析的形式）
    print(f"SCRIPT_DIR:{{current_dir}}")
    print(f"FRAMEWORK_ROOT:{{framework_root}}")
    print(f"PROJECT_ROOT:{{project_root}}")
    print(f"PROJECT_NAME:{project_name}")
    
    # 使用路径管理器验证
    path_manager = get_path_manager()
    print(f"MANAGER_FRAMEWORK_ROOT:{{path_manager.framework_root}}")
    print(f"MANAGER_PROJECT_ROOT:{{path_manager.project_root}}")
    
    # 验证项目根目录是否正确（应该是脚本所在目录）
    if project_root == current_dir:
        print("PROJECT_ROOT_CORRECT:True")
    else:
        print("PROJECT_ROOT_CORRECT:False")
    
    # 验证框架根目录是否正确
    # 框架根目录应该是包含 setup.py, veriflow, README.md 的目录
    # 对于测试环境，应该是 project_test 的父目录
    current_path = Path(current_dir)
    expected_framework = None
    
    # 向上查找，找到包含 project_test 的目录的父目录
    for parent in current_path.parents:
        if parent.name == "project_test":
            expected_framework = str(parent.parent)
            break
    
    if expected_framework and framework_root == expected_framework:
        print("FRAMEWORK_ROOT_CORRECT:True")
    else:
        print("FRAMEWORK_ROOT_CORRECT:False")

if __name__ == "__main__":
    main()
'''
        
        script_path = os.path.join(project_path, "test_script.py")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

    def _run_all_project_tests(self) -> bool:
        """运行所有项目测试脚本"""
        if not self.test_root or not os.path.exists(self.test_root):
            return False
        
        # 找到所有测试脚本
        test_scripts = []
        for root, dirs, files in os.walk(self.test_root):
            if "test_script.py" in files:
                test_scripts.append(os.path.join(root, "test_script.py"))
        
        all_passed = True
        
        for script_path in test_scripts:
            project_dir = os.path.dirname(script_path)
            relative_path = os.path.relpath(project_dir, self.test_root)
            
            try:
                # 切换到项目目录运行脚本
                result = subprocess.run(
                    [sys.executable, "test_script.py"],
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # 解析输出
                    test_result = self._parse_test_output(result.stdout, relative_path)
                    self.test_results.append(test_result)
                    
                    if not test_result['success']:
                        all_passed = False
                        print(f"测试失败 {relative_path}: {test_result['error']}")
                else:
                    all_passed = False
                    print(f"脚本执行失败 {relative_path}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                all_passed = False
                print(f"脚本执行超时: {relative_path}")
            except Exception as e:
                all_passed = False
                print(f"执行异常 {relative_path}: {e}")
        
        return all_passed

    def _parse_test_output(self, output: str, project_name: str) -> Dict:
        """解析测试脚本输出"""
        lines = output.strip().split('\n')
        result = {
            'project': project_name,
            'success': True,
            'error': None,
            'data': {}
        }
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                result['data'][key] = value
        
        # 检查关键指标
        framework_correct = result['data'].get('FRAMEWORK_ROOT_CORRECT', 'False') == 'True'
        project_correct = result['data'].get('PROJECT_ROOT_CORRECT', 'False') == 'True'
        
        if not framework_correct:
            result['success'] = False
            result['error'] = "框架根目录查找错误"
        elif not project_correct:
            result['success'] = False
            result['error'] = "项目根目录查找错误"
        
        return result

    def _cleanup_test_environment(self):
        """清理测试环境"""
        if self.test_root and os.path.exists(self.test_root):
            try:
                shutil.rmtree(self.test_root)
            except Exception:
                pass  # 忽略清理失败


if __name__ == "__main__":
    unittest.main(verbosity=2) 