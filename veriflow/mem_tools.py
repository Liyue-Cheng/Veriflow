# -*- coding: utf-8 -*-
"""
VeriFlow Memory Tools

提供用于处理内存文件的实用程序，例如 Verilog 的 $readmemh 和 $readmemb
所使用的 .mem 或 .hex 文件格式。这些工具与 VerilogBits 类型协同工作，
确保类型安全和数据完整性。
"""

import logging
from typing import List, Union, Optional
from .verilog_bits import VerilogBits
from .verilogger import logger as verilogger

logger = logging.getLogger(__name__)

class MemTools:
    """
    内存文件读写工具集
    """

    def read_mem_file(
        self, 
        file_path: str, 
        word_width: int, 
        is_hex: bool = True
    ) -> List[VerilogBits]:
        """
        从 .mem 或 .hex 文件中读取数据，并将其转换为 VerilogBits 列表。
        支持十六进制 ($readmemh) 和二进制 ($readmemb) 格式。

        :param file_path: 输入文件的路径。
        :param word_width: 每个数据字的位宽。
        :param is_hex: 如果为 True，则按十六进制解析；否则按二进制解析。
        :return: 一个包含 VerilogBits 对象的列表。
        :raises FileNotFoundError: 如果文件不存在。
        :raises ValueError: 如果文件内容格式不正确。
        """
        verilogger.title(f"Reading Memory File: {file_path}")
        logger.info(f"Reading {'hex' if is_hex else 'binary'} data from {file_path} with word width {word_width}")
        
        mem_data: List[VerilogBits] = []
        try:
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    # 去除空白字符和注释
                    line = line.strip()
                    if '@' in line: # Verilog风格的地址说明
                        line = line.split('@')[0].strip()
                    if '//' in line: # C风格的注释
                        line = line.split('//')[0].strip()
                    
                    if not line:
                        continue
                        
                    words = line.split()
                    for word in words:
                        try:
                            # 根据格式，为 bitstring 准备正确的初始化字符串
                            prefix = '0x' if is_hex else '0b'
                            value_str = prefix + word
                            
                            vb = VerilogBits(value_str, length=word_width)
                            mem_data.append(vb)
                        except Exception as e:
                            error_msg = f"Error parsing word '{word}' on line {line_num}: {e}"
                            logger.error(error_msg)
                            raise ValueError(error_msg) from e
            
            logger.info(f"Successfully read {len(mem_data)} words from {file_path}")
            return mem_data

        except FileNotFoundError:
            logger.error(f"Memory file not found: {file_path}")
            raise

    def write_mem_file(
        self,
        file_path: str,
        data: List[VerilogBits],
        is_hex: bool = True,
        words_per_line: int = 1
    ) -> None:
        """
        将 VerilogBits 列表写入到 .mem 或 .hex 文件。

        :param file_path: 输出文件的路径。
        :param data: 要写入的 VerilogBits 数据列表。
        :param is_hex: 如果为 True，则以十六进制格式写入；否则以二进制格式写入。
        :param words_per_line: 每行写入多少个数据字。
        :raises ValueError: 如果输入数据为空。
        """
        verilogger.title(f"Writing Memory File: {file_path}")
        if not data:
            raise ValueError("Input data cannot be empty.")
            
        logger.info(f"Writing {len(data)} words to {file_path} in {'hex' if is_hex else 'binary'} format.")

        with open(file_path, 'w') as f:
            for i, vb in enumerate(data):
                if is_hex:
                    # bitstring 的 .hex 属性不带 '0x' 前缀
                    value_str = vb._data.hex
                else:
                    value_str = vb.bin
                
                f.write(value_str)
                
                # 判断是否需要换行
                if (i + 1) % words_per_line == 0:
                    f.write('\n')
                else:
                    f.write(' ') # 同一行内的单词用空格隔开
        
        logger.info(f"Successfully wrote {len(data)} words to {file_path}")


# --- 便捷函数 ---

def read_memh(file_path: str, word_width: int) -> List[VerilogBits]:
    """
    便捷函数：以十六进制格式读取内存文件。
    相当于 $readmemh。

    :param file_path: 输入文件的路径。
    :param word_width: 每个数据字的位宽。
    :return: 一个包含 VerilogBits 对象的列表。
    """
    return MemTools().read_mem_file(file_path, word_width, is_hex=True)


def read_memb(file_path: str, word_width: int) -> List[VerilogBits]:
    """
    便捷函数：以二进制格式读取内存文件。
    相当于 $readmemb。

    :param file_path: 输入文件的路径。
    :param word_width: 每个数据字的位宽。
    :return: 一个包含 VerilogBits 对象的列表。
    """
    return MemTools().read_mem_file(file_path, word_width, is_hex=False)


def write_memh(file_path: str, data: List[VerilogBits], words_per_line: int = 1) -> None:
    """
    便捷函数：以十六进制格式写入内存文件。

    :param file_path: 输出文件的路径。
    :param data: 要写入的 VerilogBits 数据列表。
    :param words_per_line: 每行写入多少个数据字。
    """
    MemTools().write_mem_file(file_path, data, is_hex=True, words_per_line=words_per_line)


def write_memb(file_path: str, data: List[VerilogBits], words_per_line: int = 1) -> None:
    """
    便捷函数：以二进制格式写入内存文件。

    :param file_path: 输出文件的路径。
    :param data: 要写入的 VerilogBits 数据列表。
    :param words_per_line: 每行写入多少个数据字。
    """
    MemTools().write_mem_file(file_path, data, is_hex=False, words_per_line=words_per_line)
