"""
VeriFlow路径工具模块

提供框架根目录和项目根目录的自动查找功能，不依赖环境变量。
支持从调用文件的位置开始向上查找。
"""

import os
import inspect
from pathlib import Path
from typing import Optional, Dict


class PathFinder:
    """路径查找工具类"""
    
    # 框架根目录标记文件
    FRAMEWORK_MARKER_FILE = '.veriflow-root'
    
    # 项目根目录标记文件
    PROJECT_MARKER_FILE = '.veriflow-project'
    
    @classmethod
    def find_framework_root(cls, start_path: Optional[str] = None) -> Optional[str]:
        """
        查找框架根目录
        
        查找策略：
        仅查找包含标记文件 .veriflow-root 的目录
        
        Args:
            start_path: 开始查找的路径，默认为调用文件所在目录
            
        Returns:
            框架根目录的绝对路径，如果未找到返回None
        """
        if start_path is None:
            start_path = cls._get_caller_directory()
        
        start_path = Path(start_path).resolve()
        
        # 向上查找，直到文件系统根目录
        for current in [start_path] + list(start_path.parents):
            # 查找标记文件
            if cls._has_framework_marker_file(current):
                return str(current)
        
        return None
    
    @classmethod
    def find_project_root(cls, start_path: Optional[str] = None) -> Optional[str]:
        """
        查找项目根目录
        
        查找策略：
        仅查找包含标记文件 .veriflow-project 的目录
        
        Args:
            start_path: 开始查找的路径，默认为调用文件所在目录
            
        Returns:
            项目根目录的绝对路径，如果未找到返回None
        """
        if start_path is None:
            start_path = cls._get_caller_directory()
        
        start_path = Path(start_path).resolve()
        
        # 向上查找，直到文件系统根目录
        for current in [start_path] + list(start_path.parents):
            # 查找项目标记文件
            if cls._has_project_marker_file(current):
                return str(current)
        
        return None
    
    @classmethod
    def _has_framework_marker_file(cls, path: Path) -> bool:
        """检查是否包含框架标记文件"""
        return (path / cls.FRAMEWORK_MARKER_FILE).exists()
    
    @classmethod
    def _has_project_marker_file(cls, path: Path) -> bool:
        """检查是否包含项目标记文件"""
        return (path / cls.PROJECT_MARKER_FILE).exists()
    
    
    @classmethod
    def _get_caller_directory(cls) -> str:
        """
        获取调用者的文件所在目录
        
        Returns:
            调用者文件所在目录的绝对路径
        """
        try:
            # 获取调用栈，跳过当前方法
            frame = inspect.currentframe()
            # 跳过 _get_caller_directory 和 find_framework_root/find_project_root
            for _ in range(3):
                frame = frame.f_back
                if frame is None:
                    break
            
            if frame is not None:
                caller_file = frame.f_code.co_filename
                return os.path.dirname(os.path.abspath(caller_file))
        except (AttributeError, OSError):
            pass
        
        # 如果无法获取调用者信息，回退到当前工作目录
        return os.getcwd()


class PathManager:
    """路径管理器类"""
    
    def __init__(self, start_path: Optional[str] = None):
        """
        初始化路径管理器
        
        Args:
            start_path: 开始查找的路径，默认为调用文件所在目录
        """
        if start_path is None:
            start_path = PathFinder._get_caller_directory()
        self.start_path = start_path
        self._framework_root = None
        self._project_root = None
        self._paths_cache = {}
    
    @property
    def framework_root(self) -> Optional[str]:
        """获取框架根目录"""
        if self._framework_root is None:
            self._framework_root = PathFinder.find_framework_root(self.start_path)
        return self._framework_root
    
    @property
    def project_root(self) -> Optional[str]:
        """获取项目根目录"""
        if self._project_root is None:
            self._project_root = PathFinder.find_project_root(self.start_path)
        return self._project_root
    
    def get_framework_path(self, *sub_paths) -> Optional[str]:
        """
        获取框架内的路径
        
        Args:
            *sub_paths: 子路径组件
            
        Returns:
            完整路径，如果框架根目录未找到返回None
        """
        if self.framework_root is None:
            return None
        
        return os.path.join(self.framework_root, *sub_paths)
    
    def get_project_path(self, *sub_paths) -> Optional[str]:
        """
        获取项目内的路径
        
        Args:
            *sub_paths: 子路径组件
            
        Returns:
            完整路径，如果项目根目录未找到返回None
        """
        if self.project_root is None:
            return None
        
        return os.path.join(self.project_root, *sub_paths)
    
    def get_standard_paths(self) -> Dict[str, Optional[str]]:
        """
        获取标准路径字典
        
        Returns:
            包含常用路径的字典
        """
        return {
            'framework_root': self.framework_root,
            'project_root': self.project_root,
            'veriflow_core': self.get_framework_path('veriflow'),
            'projects_dir': self.get_framework_path('projects'),
            'simulator_dir': self.get_framework_path('simulator'),
            'utils_dir': self.get_framework_path('utils'),
            'references_dir': self.get_framework_path('references'),
            'project_rtl': self.get_project_path('rtl'),
            'project_tb': self.get_project_path('tb'),
            'project_sim_outputs': self.get_project_path('sim_outputs'),
            'project_data': self.get_project_path('data'),
            'project_matlab': self.get_project_path('matlab'),
            'project_python': self.get_project_path('python'),
        }
    
    def validate_paths(self) -> Dict[str, bool]:
        """
        验证路径是否存在
        
        Returns:
            路径验证结果字典
        """
        paths = self.get_standard_paths()
        return {
            name: os.path.exists(path) if path else False
            for name, path in paths.items()
        }
    
    def create_project_structure(self, project_name: str) -> bool:
        """
        在projects目录下创建标准的项目结构
        
        Args:
            project_name: 项目名称
            
        Returns:
            创建是否成功
        """
        if self.framework_root is None:
            return False
        
        project_path = self.get_framework_path('projects', project_name)
        if os.path.exists(project_path):
            return False  # 项目已存在
        
        # 创建标准目录结构
        standard_dirs = ['rtl', 'tb', 'sim_outputs', 'data', 'matlab', 'python']
        
        try:
            os.makedirs(project_path)
            
            for dir_name in standard_dirs:
                os.makedirs(os.path.join(project_path, dir_name))
            
            # 创建项目标记文件
            marker_file = os.path.join(project_path, PathFinder.PROJECT_MARKER_FILE)
            with open(marker_file, 'w') as f:
                f.write(f'# VeriFlow项目: {project_name}\n')
            
            return True
            
        except OSError:
            return False


# 便捷函数
def find_framework_root(start_path: Optional[str] = None) -> Optional[str]:
    """
    查找框架根目录的便捷函数
    
    Args:
        start_path: 开始查找的路径，默认为调用文件所在目录
    """
    return PathFinder.find_framework_root(start_path)


def find_project_root(start_path: Optional[str] = None) -> Optional[str]:
    """
    查找项目根目录的便捷函数
    
    Args:
        start_path: 开始查找的路径，默认为调用文件所在目录
    """
    return PathFinder.find_project_root(start_path)


def get_path_manager(start_path: Optional[str] = None) -> PathManager:
    """
    获取路径管理器实例的便捷函数
    
    Args:
        start_path: 开始查找的路径，默认为调用文件所在目录
    """
    return PathManager(start_path) 