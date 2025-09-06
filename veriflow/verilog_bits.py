# -*- coding: utf-8 -*-
# file: veriflow/verilog_bits.py

#由于本模块对初学者来说比较复杂，因此所有的注释都是中文的，AI修改的时候请保留中文注释。

"""
VerilogBits: A strongly-typed, Verilog-style bit vector class.
一个强类型、类似Verilog风格的位向量类。
这个模块的核心是 VerilogBits 类，它旨在模拟硬件描述语言(HDL)中常见的位向量行为，
同时利用Python的强大功能。其关键特性是“强类型”，意味着它不允许与Python
内建的整数或字符串类型进行隐式的混合运算，从而避免了在硬件仿真和软件验证中
常见的微妙错误。
"""

# 导入 bitstring 库。这是本模块的核心依赖。
# bitstring 是一个功能强大的第三方Python库，专门用于处理二进制数据。
# 它提供了灵活的创建、解析和操作位、字节和十六进制数据的功能。
import bitstring
# 从 typing 模块导入 Union 和 Optional。
# 这些是Python的“类型提示”(Type Hinting)功能的一部分，用于提高代码的可读性和可维护性。
# 它们本身在运行时没有强制效果(除非使用像mypy这样的静态检查工具)，但能告诉开发者
# 函数或变量期望什么类型的数据。
# Union: 表示一个值可以是多种类型之一。例如 Union[int, str] 表示可以是整数或字符串。
# Optional: 表示一个值可以是指定的类型，或者是 None。Optional[int] 等同于 Union[int, None]。
from typing import Union, Optional

class VerilogBits:
    """
    A strongly encapsulated bit vector that mimics Verilog's [MSB:LSB] slicing
    and behavior, while preventing implicit conversions and unintended operations
    with other Python types.
    一个强封装的位向量，它模仿Verilog的[MSB:LSB]（高位在前，低位在后）的切片
    和行为，同时防止与其他Python类型进行隐式转换和意外操作。
    
    The internal data is stored in a private bitstring.BitArray, and access is
    tightly controlled through explicitly defined methods.
    内部数据存储在一个私有的 bitstring.BitArray 对象中，并通过明确定义的方法
    进行严格控制的访问。
    “私有” (private) 在Python中是一个约定，通过在属性名前加一个下划线 `_` (例如 `_data`) 来表示。
    这告诉其他开发者这个属性是内部实现细节，不应该在类的外部直接访问。
    """

    # 这是类的构造函数，也叫初始化方法。当创建一个新的VerilogBits对象时 (例如 `vb = VerilogBits(...)`)，
    # Python会自动调用这个 __init__ 方法。
    # - self: 这是对实例本身的引用，必须是实例方法的第一个参数。Python会自动传入它。
    # - value: 创建位向量的初始值。类型提示 `Union[int, str, 'VerilogBits', bitstring.BitArray, None]` 
    #   表示 value 参数可以接受整数、字符串、另一个VerilogBits对象、一个bitstring库的BitArray对象，或者None。
    #   `'VerilogBits'` 使用引号是因为在定义类的时候，类本身还没有完全被定义，用字符串可以避免引用错误。
    # - length: 位向量的期望长度（位数）。类型提示 `Optional[int]` 表示它可以是一个整数，也可以是None（未指定）。
    # - signed: 一个布尔标志，指示当从整数创建时，是否应将其解释为有符号数。
    def __init__(self, value: Union[int, str, 'VerilogBits', bitstring.BitArray, None] = None, length: Optional[int] = None, signed: bool = False):
        # --- Python面向对象编程：isinstance() ---
        # isinstance(object, classinfo) 是Python的内建函数，用于检查一个对象是否是指定类或其子类的实例。
        # 这里用它来判断传入的 `value` 是哪种类型，以便进行相应的处理。
        
        # 1. 如果 `value` 是另一个 VerilogBits 实例，我们创建一个它的内部 `_data` 的副本。
        #    这被称为“拷贝构造”，确保新的对象与原始对象独立，修改一个不会影响另一个。
        if isinstance(value, VerilogBits):
            self._data = value._data.copy()
        # 2. 如果 `value` 是一个 bitstring.BitArray 对象（这通常用于内部操作），直接使用它。
        elif isinstance(value, bitstring.BitArray):
            self._data = value
        # 3. 如果 `value` 是一个整数，根据 `signed` 标志来决定如何创建位向量。
        #    `length` 参数在这里非常重要，它决定了生成的位向量的长度。
        elif isinstance(value, int):
             # 如果 signed 为 True，使用 'int' (有符号) 创建；否则使用 'uint' (无符号)。
             keyword = 'int' if signed else 'uint'
             self._data = bitstring.BitArray(**{keyword: value, 'length': length})
        # 4. 对于其他情况（主要是字符串，如 '0b1101' 或 '0xFF'），让 bitstring 库自动检测格式。
        else:
            # 首先让 bitstring 根据 value 的内容创建一个 BitArray。
            # bitstring 很智能，可以自动识别 '0b', '0x', '0o' 等前缀。
            self._data = bitstring.BitArray(value)
            # 然后，如果用户指定了 `length`，我们需要进行检查和调整。
            if length is not None:
                # 如果创建的位向量比期望的长，就进行截断。
                # `self._data[-length:]` 是Python的切片语法，表示从后面数第 `length` 个元素到末尾，
                # 效果就是只保留低 `length` 位。
                if len(self._data) > length:
                    self._data = self._data[-length:]
                # 如果创建的位向量比期望的短，就在前面补0（左填充）。
                # `prepend` 是 bitstring 的方法，用于在位向量的开头添加内容。
                # `f'uint:{length - len(self._data)}=0'` 是Python的 f-string 格式化字符串。
                # 它会动态地计算出需要补零的位数，并生成类似 'uint:4=0' 的字符串，
                # bitstring 知道这表示“添加4个值为0的无符号位”。
                elif len(self._data) < length:
                    self._data.prepend(f'uint:{length - len(self._data)}=0')

    # --- Python语法糖：@property ---
    # `@property` 是一个装饰器 (decorator)。装饰器是一种特殊的函数，可以修改或增强另一个函数或类的行为。
    # `@property` 可以让一个方法像属性一样被访问，即调用时不需要加括号 `()`。
    # 例如，我们可以写 `my_bits.bin` 而不是 `my_bits.bin()`。
    @property
    def bin(self) -> str:
        """Returns the binary representation as a string."""
        # 返回内部 _data 对象 (bitstring.BitArray) 的二进制字符串表示。
        return self._data.bin

    @property
    def uint(self) -> int:
        """Returns the unsigned integer representation."""
        # 返回内部 _data 对象的无符号整数表示。
        return self._data.uint

    @property
    def sint(self) -> int:
        """Returns the signed integer representation (2's complement)."""
        # 返回内部 _data 对象的有符号整数表示（补码）。
        return self._data.int
        
    # --- Python的魔法方法 (Magic Methods / Dunder Methods) ---
    # 以双下划线开头和结尾的方法（如 `__len__`, `__getitem__`）被称为魔法方法。
    # 它们使得自定义的类可以支持Python的内建操作。
    # 例如，实现了 `__len__` 后，我们就可以对 VerilogBits 对象使用 `len()` 函数。
    def __len__(self) -> int:
        """Returns the length of the bit vector."""
        return len(self._data)

    def _parse_verilog_slice(self, key: slice) -> tuple[int, int]:
        """
        一个内部辅助方法，用于将Verilog风格的切片 (e.g., [7:0]) 转换为Python
        bitstring库可以理解的切片 (e.g., [0:8])。
        - Verilog: [MSB:LSB] (高位:低位)，索引从右到左增加。
        - Python:  [start:end] (从头开始的索引)，索引从左到右增加。
        """
        # slice 对象有 start, stop, step 属性。对于 `[7:0]`，key.start 是 7，key.stop 是 0。
        msb, lsb = key.start, key.stop
        # 检查索引是否为整数。
        if not (isinstance(msb, int) and isinstance(lsb, int)):
            raise TypeError("Verilog-style slice indices must be integers.")
        # 在Verilog风格中，LSB不能大于MSB。
        if lsb > msb:
            raise ValueError(f"LSB ({lsb}) cannot be greater than MSB ({msb}) in Verilog-style slicing.")
        # 获取位向量的总长度。
        bit_length = len(self)
        # 最高有效位的索引是 `长度 - 1`。
        max_index = bit_length - 1
        # 检查索引是否越界。
        if not (0 <= msb <= max_index and 0 <= lsb <= max_index):
            raise IndexError(f"Slice indices [{msb}:{lsb}] are out of bounds for a {bit_length}-bit array (0 to {max_index}).")
        
        # --- 核心转换逻辑 ---
        # 假设一个8位向量 'abcdefgh'，长度为8，索引为 [7:0]。
        # Verilog [7:4] 应该是 'abcd'。
        # 对应的Python索引：
        # bit_length = 8, msb = 7, lsb = 4
        # start = 8 - 1 - 7 = 0
        # end = 8 - 1 - 4 + 1 = 4
        # Python切片 `[0:4]` 得到的就是前4个元素，即 'abcd'。
        start = bit_length - 1 - msb
        end = bit_length - 1 - lsb + 1
        # 返回一个元组 (tuple)，包含转换后的Python风格的起始和结束索引。
        return start, end

    # 实现了 `__getitem__` 方法后，对象就支持索引和切片操作，就像列表或字符串一样。
    # 例如 `my_bits[3]` 或 `my_bits[7:0]`。
    def __getitem__(self, key: Union[int, slice]) -> 'VerilogBits':
        if isinstance(key, slice):
            # Verilog切片不支持步长 (step)，如 `[7:0:2]`。
            if key.step is not None:
                raise ValueError("Step is not supported in Verilog-style slicing.")
            # 调用内部方法转换索引。
            py_start, py_end = self._parse_verilog_slice(key)
            # 使用转换后的索引对内部的 bitstring.BitArray 进行切片。
            # `slice(py_start, py_end)` 创建一个Python的 slice 对象。
            new_val = self._data.__getitem__(slice(py_start, py_end))
            # 将切片结果（也是一个BitArray）包装成一个新的 VerilogBits 对象返回，
            # 保持了类型的强封装性。
            return VerilogBits(new_val)
        elif isinstance(key, int):
            # 为了保持类型一致性，即使是访问单个位，也返回一个长度为1的 VerilogBits 对象。
            # 这与Verilog中 `wire a; a = b[3];` 的行为类似，结果仍然是一个 "wire"。
            new_val = self._data.__getitem__(slice(key, key + 1))
            return VerilogBits(new_val)
        else:
            # 如果索引类型不被支持，抛出类型错误。
            raise TypeError(f"Index must be an integer or slice, not {type(key).__name__}")

    # 实现了 `__setitem__` 方法后，对象就支持赋值操作。
    # 例如 `my_bits[3] = 1` 或 `my_bits[7:0] = '0xFF'`。
    def __setitem__(self, key: Union[int, slice], value: Union[int, str, 'VerilogBits']):
        # 首先，将传入的 `value` （无论它是整数、字符串还是VerilogBits）
        # 也转换成一个 VerilogBits 对象。这是一种“规范化”输入的技巧，
        # 使得后续代码可以统一处理 `normalized_value._data`。
        normalized_value = VerilogBits(value)
        value_to_set = normalized_value._data
        
        if isinstance(key, slice):
            # 同样不支持步长。
            if key.step is not None:
                raise ValueError("Step is not supported in Verilog-style slicing.")
            # 转换索引。
            py_start, py_end = self._parse_verilog_slice(key)
            # 对内部的 bitstring 对象进行赋值。
            self._data[slice(py_start, py_end)] = value_to_set
        elif isinstance(key, int):
            # 对单个位进行赋值。
            self._data[key] = value_to_set
        else:
            raise TypeError(f"Index must be an integer or slice, not {type(key).__name__}")
    
    # 实现了 `__eq__` 方法后，对象就可以使用 `==` 运算符进行比较。
    def __eq__(self, other: object) -> bool:
        """
        Explicitly compares this VerilogBits with another.
        Only returns True if the other object is also a VerilogBits instance
        and their binary values are identical.
        显式地将此VerilogBits与另一个对象进行比较。
        仅当另一个对象也是VerilogBits的实例，并且它们的二进制值相同时，才返回True。
        """
        # --- Python的类型安全实践 ---
        # 首先检查 `other` 是否是 VerilogBits 类型。
        if not isinstance(other, VerilogBits):
            # `NotImplemented` 是一个特殊的返回值。它告诉Python的解释器，
            # VerilogBits不知道如何与 `other` 的类型进行比较。
            # 如果 `other` 也有 `__eq__` 方法，Python会尝试调用 `other.__eq__(self)`。
            # 这比直接返回 `False` 更准确，因为它允许其他类来定义与VerilogBits的比较逻辑。
            return NotImplemented
        # 如果类型匹配，就比较它们内部的 `_data`。
        return self._data == other._data

    # `+` 运算符已被禁用，请使用 VerilogBits.concat() 方法。
    def __add__(self, other: 'VerilogBits') -> 'VerilogBits':
        """
        The '+' operator is explicitly disabled to promote clear and explicit
        concatenation via the `VerilogBits.concat()` method.
        显式禁用 '+' 运算符，以鼓励使用更清晰的 `VerilogBits.concat()` 方法进行拼接。
        """
        raise TypeError("The '+' operator is disabled. Please use VerilogBits.concat() for explicit concatenation.")

    # `__repr__` 方法返回对象的“官方”字符串表示形式。
    # 理想情况下，`eval(repr(obj))` 应该能重新创建出这个对象。
    def __repr__(self) -> str:
        # 返回一个清晰的、能表明如何创建此对象的字符串。
        return f"VerilogBits('{self._data.bin}')"

    def replicate(self, n: int) -> 'VerilogBits':
        """
        Replicates the bit vector `n` times, mimicking Verilog's {n{...}} syntax.
        将位向量复制 `n` 次，模拟 Verilog 的 `{n{...}}` 语法。

        :param n: The number of times to replicate the bit vector. (复制次数)
        :return: A new VerilogBits object containing the replicated data.
        """
        if not isinstance(n, int) or n < 0:
            raise ValueError("Replication count must be a non-negative integer.")
        # 使用 bitstring 的乘法操作来实现复制，然后包装成新的 VerilogBits 对象。
        return VerilogBits(self._data * n)

    @classmethod
    def concat(cls, *args: 'VerilogBits') -> 'VerilogBits':
        """
        Concatenates multiple VerilogBits objects together.
        将多个 VerilogBits 对象拼接在一起。

        This method serves as an explicit replacement for the disabled '+' operator.
        此方法是禁用的 '+' 运算符的明确替代品。

        :param args: A variable number of VerilogBits objects to concatenate. (要拼接的多个VerilogBits对象)
        :return: A new VerilogBits object representing the concatenation of all inputs.
        """
        # 创建一个空的 bitstring.BitArray 来存放拼接结果。
        concatenated_data = bitstring.BitArray()
        # 遍历所有传入的参数。
        for i, arg in enumerate(args):
            # 确保每个参数都是 VerilogBits 的实例。
            if not isinstance(arg, VerilogBits):
                raise TypeError(f"Argument {i} is not a VerilogBits instance, but {type(arg).__name__}")
            # 将每个参数的内部 _data 拼接到结果上。
            concatenated_data += arg._data
        # 使用拼接后的数据创建一个新的 VerilogBits 实例。
        return cls(concatenated_data)

    # --- IOC (Inversion of Control) 的一种体现：明确禁用行为 ---
    # Python的哲学是"我们都是成年人"，默认不会隐藏太多东西。但在这里，为了实现
    # 强类型和模拟Verilog的行为，我们故意"控制反转"，明确地禁用那些我们不希望
    # VerilogBits对象拥有的默认Python行为。
    # 我们通过重写这些魔法方法并让它们抛出 `TypeError` 来实现这一点。
    # 这是一种非常主动和明确的设计选择，用来强制执行类的设计意图。
    
    # --- 明确禁用不支持的操作 ---
    # 根据Verilog 2001标准，位向量之间的比较运算应当按位进行
    # 目前这些功能暂未实现，因此禁用以防止bug
    def __lt__(self, other): raise TypeError("Comparison operators (<, >, <=, >=) are not supported yet.")
    def __le__(self, other): raise TypeError("Comparison operators (<, >, <=, >=) are not supported yet.")
    def __gt__(self, other): raise TypeError("Comparison operators (<, >, <=, >=) are not supported yet.")
    def __ge__(self, other): raise TypeError("Comparison operators (<, >, <=, >=) are not supported yet.")
    
    # 根据Verilog 2001标准，位向量之间的算术运算应当按照二进制补码进行
    # 目前这些功能暂未实现，因此禁用以防止bug
    def __sub__(self, other): raise TypeError("Arithmetic operators (-, *, /, etc.) are not supported yet.")
    def __rsub__(self, other): raise TypeError("Arithmetic operators (-, *, /, etc.) are not supported yet.")
    def __mul__(self, other): raise TypeError("Arithmetic operators (-, *, /, etc.) are not supported yet.")
    def __rmul__(self, other): raise TypeError("Arithmetic operators (-, *, /, etc.) are not supported yet.")
    def __truediv__(self, other): raise TypeError("Arithmetic operators (-, *, /, etc.) are not supported yet.")
    def __rtruediv__(self, other): raise TypeError("Arithmetic operators (-, *, /, etc.) are not supported yet.")
    
    # 根据Verilog 2001标准，位向量之间的位运算应当按位进行
    # 目前这些功能暂未实现，因此禁用以防止bug
    def __and__(self, other): raise TypeError("Bitwise operators (&, |, ^, ~) are not supported yet.")
    def __rand__(self, other): raise TypeError("Bitwise operators (&, |, ^, ~) are not supported yet.")
    def __or__(self, other): raise TypeError("Bitwise operators (&, |, ^, ~) are not supported yet.")
    def __ror__(self, other): raise TypeError("Bitwise operators (&, |, ^, ~) are not supported yet.")
    def __xor__(self, other): raise TypeError("Bitwise operators (&, |, ^, ~) are not supported yet.")
    def __rxor__(self, other): raise TypeError("Bitwise operators (&, |, ^, ~) are not supported yet.")
    def __invert__(self): raise TypeError("Bitwise operators (&, |, ^, ~) are not supported yet.")

    # 禁用隐式类型转换
    # 不允许 `int(my_bits)` 这样的隐式转换。
    def __int__(self): raise TypeError("Implicit conversion to int is not supported. Use .uint property.")
    # `__str__` 方法返回对象的"非官方"或用户友好的字符串表示。
    # 当调用 `print(obj)` 或 `str(obj)` 时会用到。这里让它和 `__repr__` 行为一致。
    def __str__(self): return self.__repr__()
