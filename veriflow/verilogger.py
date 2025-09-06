"""
Verilogger - EDA-style logging and reporting system

Provides ready-to-use logging and reporting functionality designed for hardware 
design and verification workflows. Built on loguru with support for leveled 
logging, plain text output, table generation, and more.
"""

import sys
import os
import functools
import traceback
import threading
from typing import List, Optional, Union, Any, Dict, Set
from loguru import logger as _loguru_logger


class Verilogger:
    """
    EDA-style logger and report generator
    
    Features:
    - Ready to use out of the box, no initialization required
    - Unified output management (console + file)
    - Leveled logging and plain text output
    - EDA-style report generation (titles, separators, tables)
    - Automatic error/warning statistics tracking
    - Exception catching and summary reporting
    """
    
    def __init__(self):
        """Initialize Verilogger instance"""
        # Remove loguru's default handler
        _loguru_logger.remove()
        
        # Add console handler with color support
        _loguru_logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            level="DEBUG",
            colorize=True
        )
        
        # Internal statistics counters
        self._error_count = 0
        self._warning_count = 0
        
        # Unified output management
        self._output_files = []  # Store file output info {path: str, handle: file, loguru_id: int}
        self._added_files: Set[str] = set()  # Track added file paths for idempotency
        
        # Create custom write handlers list
        self._write_handlers = [self._console_write]
        
        # Thread safety lock for write operations
        self._write_lock = threading.RLock()
    
    def _console_write(self, message: str) -> None:
        """Write to console"""
        sys.stderr.write(message)
        sys.stderr.flush()
    
    def _file_write(self, message: str) -> None:
        """Write to all added files"""
        for file_info in self._output_files:
            file_info['handle'].write(message)
            file_info['handle'].flush()
    
    def add(self, file_path: str, mode: str = 'w') -> None:
        """
        Add file output target, all subsequent output will be written to the file.
        This method is idempotent - calling it multiple times with the same file path
        will not create duplicate handlers.
        
        Args:
            file_path: File path
            mode: Write mode, 'w' for overwrite, 'a' for append
        """
        with self._write_lock:
            # Check for idempotency - if file already added, skip
            if file_path in self._added_files:
                self.warning(f"File '{file_path}' is already added to output targets, skipping duplicate.")
                return
            
            # Ensure directory exists before creating file
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except OSError as e:
                    self.error(f"Failed to create directory '{directory}': {e}")
                    return
            
            # Open file for plain text writing
            try:
                file_handle = open(file_path, mode, encoding='utf-8', buffering=1)
            except OSError as e:
                self.error(f"Failed to open file '{file_path}': {e}")
                return
            
            # Add the same file handle to loguru to ensure synchronized output
            loguru_id = _loguru_logger.add(
                file_handle,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
                level="DEBUG",
                enqueue=False  # Disable queue to ensure synchronization
            )
            
            # Store file information
            file_info = {
                'path': file_path,
                'handle': file_handle,
                'loguru_id': loguru_id
            }
            self._output_files.append(file_info)
            self._added_files.add(file_path)  # Track this file as added
            
            # Add file writing to handlers if this is the first file
            if len(self._output_files) == 1:
                self._write_handlers.append(self._file_write)
    
    # === Leveled logging methods ===
    
    def debug(self, message: str) -> None:
        """Record debug level log"""
        _loguru_logger.debug(message)
    
    def info(self, message: str) -> None:
        """Record info level log"""
        _loguru_logger.info(message)
    
    def success(self, message: str) -> None:
        """Record success level log (Verilogger special feature)"""
        _loguru_logger.success(message)
    
    def warning(self, message: str) -> None:
        """Record warning level log with automatic counting (thread-safe)"""
        with self._write_lock:
            self._warning_count += 1
        _loguru_logger.warning(message)
    
    def error(self, message: str) -> None:
        """Record error level log with automatic counting (thread-safe)"""
        with self._write_lock:
            self._error_count += 1
        _loguru_logger.error(message)
    
    def critical(self, message: str) -> None:
        """Record critical error level log with automatic counting (thread-safe)"""
        with self._write_lock:
            self._error_count += 1
        _loguru_logger.critical(message)
    
    # === Plain text writing methods ===
    
    def write(self, message: str) -> None:
        """
        Plain text writing without any formatting (thread-safe)
        
        Args:
            message: Message to write, output as-is
        """
        with self._write_lock:
            for handler in self._write_handlers:
                handler(message)
    
    def writeln(self, message: str = '') -> None:
        """
        Plain text writing with newline
        
        Args:
            message: Message to write
        """
        self.write(message + '\n')
    
    # === EDA-style report generation methods ===
    
    def title(self, text: str, width: int = 80, char: str = '=') -> None:
        """
        Generate title block with border and centered text
        
        Args:
            text: Title text
            width: Total width
            char: Border character
        """
        border = char * width
        title_line = f"{text:^{width}}"
        
        self.writeln()
        self.writeln(border)
        self.writeln(title_line)
        self.writeln(border)
        self.writeln()
    
    def subtitle(self, text: str, width: int = 80, char: str = '-') -> None:
        """
        生成一行子标题，带前后装饰
        
        Args:
            text: 子标题文本
            width: 总宽度
            char: 装饰字符
        """
        # 计算文本显示宽度
        text_width = self._get_display_width(text)
        
        # 计算装饰线长度，确保总宽度不超过指定宽度
        available_width = width - text_width - 4  # 4个字符用于空格和装饰
        if available_width < 4:
            available_width = 4
        
        left_decor = char * (available_width // 2)
        right_decor = char * (available_width - available_width // 2)
        
        subtitle_line = f"{left_decor} {text} {right_decor}"
        self.writeln()
        self.writeln(subtitle_line)
        self.writeln()

    
    def separator(self, char: str = '-', width: int = 80) -> None:
        """
        打印一行水平分隔符
        
        Args:
            char: 分隔符字符
            width: 分隔符宽度
        """
        self.writeln(char * width)
    
    def _get_display_width(self, text: str) -> int:
        """
        计算文本的显示宽度，考虑中文字符占用2个字符宽度
        
        Args:
            text: 输入文本
            
        Returns:
            显示宽度
        """
        width = 0
        for char in text:
            # 中文字符、全角字符等占用2个字符宽度
            if ord(char) > 127:
                width += 2
            else:
                width += 1
        return width
    
    def _pad_text(self, text: str, width: int, align: str = 'left') -> str:
        """
        填充文本到指定宽度，考虑中文字符的显示宽度
        
        Args:
            text: 原文本
            width: 目标宽度
            align: 对齐方式 ('left', 'right', 'center')
            
        Returns:
            填充后的文本
        """
        display_width = self._get_display_width(text)
        padding_needed = max(0, width - display_width)
        
        if align == 'left':
            return text + ' ' * padding_needed
        elif align == 'right':
            return ' ' * padding_needed + text
        else:  # center
            left_pad = padding_needed // 2
            right_pad = padding_needed - left_pad
            return ' ' * left_pad + text + ' ' * right_pad
    
    def table(self, headers: List[str], rows: List[List[Any]], 
              min_width: int = 8, padding: int = 2) -> None:
        """
        生成格式化的文本表格，支持中文字符正确对齐
        
        Args:
            headers: 表头列表
            rows: 数据行列表，每行是一个列表
            min_width: 每列的最小宽度
            padding: 列间填充空格数（每列左右各padding//2个空格）
        """
        if not headers or not rows:
            self.writeln("Empty table")
            return
        
        # 计算每列的最大显示宽度
        col_widths = []
        for i, header in enumerate(headers):
            max_width = max(self._get_display_width(str(header)), min_width)
            for row in rows:
                if i < len(row):
                    cell_width = self._get_display_width(str(row[i]))
                    max_width = max(max_width, cell_width)
            col_widths.append(max_width)
        
        # 计算填充
        left_pad = padding // 2
        right_pad = padding - left_pad
        
        # 生成分隔线 - 每列宽度 = 内容宽度 + 左填充 + 右填充
        separator_parts = []
        for width in col_widths:
            separator_parts.append('-' * (width + left_pad + right_pad))
        separator_line = '+' + '+'.join(separator_parts) + '+'
        
        # 打印表格
        self.writeln(separator_line)
        
        # 打印表头
        header_parts = []
        for i, header in enumerate(headers):
            padded_content = self._pad_text(str(header), col_widths[i], 'left')
            header_parts.append(' ' * left_pad + padded_content + ' ' * right_pad)
        header_line = '|' + '|'.join(header_parts) + '|'
        self.writeln(header_line)
        self.writeln(separator_line)
        
        # 打印数据行
        for row in rows:
            row_parts = []
            for i in range(len(headers)):
                cell_value = str(row[i]) if i < len(row) else ''
                padded_content = self._pad_text(cell_value, col_widths[i], 'left')
                row_parts.append(' ' * left_pad + padded_content + ' ' * right_pad)
            row_line = '|' + '|'.join(row_parts) + '|'
            self.writeln(row_line)
        
        self.writeln(separator_line)
        self.writeln()
    
    # === 统计与自动化功能 ===
    
    def get_error_count(self) -> int:
        """Get error count (thread-safe)"""
        with self._write_lock:
            return self._error_count
    
    def get_warning_count(self) -> int:
        """Get warning count (thread-safe)"""
        with self._write_lock:
            return self._warning_count
    
    def summary(self) -> None:
        """
        Print execution summary report
        """
        self.title("Execution Summary Report", width=60)
        
        # Create statistics table
        headers = ["Type", "Count", "Status"]
        rows = [
            ["ERROR", self._error_count, "FAIL" if self._error_count > 0 else "PASS"],
            ["WARNING", self._warning_count, "WARN" if self._warning_count > 0 else "PASS"]
        ]
        
        self.table(headers, rows)
        
        # Overall status assessment
        if self._error_count == 0 and self._warning_count == 0:
            self.success("Execution completed successfully with no errors or warnings.")
        elif self._error_count == 0:
            self.warning(f"Execution completed with {self._warning_count} warning(s) to review.")
        else:
            self.error(f"Execution completed with {self._error_count} error(s) and {self._warning_count} warning(s).")
    
    def catch(self, reraise: bool = False):
        """
        Exception catching decorator
        
        Args:
            reraise: Whether to re-raise the exception
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Detailed exception report
                    exc_info = traceback.format_exc()
                    self.critical(f"Unhandled exception in function {func.__name__}:")
                    self.write(f"\nException type: {type(e).__name__}\n")
                    self.write(f"Exception message: {str(e)}\n")
                    self.write(f"Detailed traceback:\n{exc_info}\n")
                    
                    if args:
                        self.write(f"Function arguments: {args}\n")
                    if kwargs:
                        self.write(f"Keyword arguments: {kwargs}\n")
                    
                    if reraise:
                        raise
                    return None
            return wrapper
        return decorator
    
    def __del__(self):
        """Clean up resources"""
        try:
            with self._write_lock:
                for file_info in self._output_files:
                    try:
                        # Remove loguru handler
                        _loguru_logger.remove(file_info['loguru_id'])
                        # Close file handle
                        file_info['handle'].close()
                    except:
                        pass
                
                # Clear tracking sets
                self._output_files.clear()
                self._added_files.clear()
        except:
            # In case _write_lock is already destroyed during shutdown
            pass


# === 全局实例 - 即时可用性 ===

# 创建全局预配置的 logger 实例
logger = Verilogger()
