# -*- coding: utf-8 -*-
# file: veriflow/internal_test/test_verilog_bits.py

import unittest
from veriflow.verilog_bits import VerilogBits

class TestVerilogBitsStrict(unittest.TestCase):
    """
    Unit tests for the final, strongly-typed VerilogBits class.
    """

    def test_creation(self):
        """Test object creation and basic properties."""
        v = VerilogBits(value=170, length=8)
        self.assertEqual(v.bin, '10101010')
        self.assertEqual(v.uint, 170)
        self.assertEqual(len(v), 8)

        v2 = VerilogBits('0b1100')
        self.assertEqual(v2.uint, 12)
        
        v3 = VerilogBits(v2)
        self.assertEqual(v3.bin, '1100')
        self.assertIsNot(v3._data, v2._data) # Should be a copy

    def test_valid_slicing_getitem(self):
        """Test valid Verilog-style slicing for __getitem__."""
        v = VerilogBits(value=170, length=8)  # 0b10101010
        self.assertEqual(v[7:4].bin, '1010')
        self.assertEqual(v[3:0].bin, '1010')
        self.assertEqual(v[5:2].bin, '1010')
        self.assertEqual(v[0:0].bin, '0')
        
    def test_valid_slicing_setitem(self):
        """Test valid Verilog-style slicing for __setitem__."""
        v = VerilogBits(length=8)
        v[7:4] = VerilogBits(value='0b1111')
        self.assertEqual(v.bin, '11110000')
        v[3:0] = '0b1010'
        self.assertEqual(v.bin, '11111010')

    def test_explicit_concatenation(self):
        """Test concatenation with the VerilogBits.concat() class method."""
        v1 = VerilogBits('0b1111')
        v2 = VerilogBits('0b0000')
        v3 = VerilogBits('0b1010')
        # Test concatenating two
        result1 = VerilogBits.concat(v1, v2)
        self.assertEqual(result1.bin, '11110000')
        self.assertIsInstance(result1, VerilogBits)
        # Test concatenating three
        result2 = VerilogBits.concat(v1, v2, v3)
        self.assertEqual(result2.bin, '111100001010')
        self.assertIsInstance(result2, VerilogBits)

    def test_replication(self):
        """Test the replicate() method."""
        v1 = VerilogBits('0b10')
        replicated = v1.replicate(4)
        self.assertEqual(replicated.bin, '10101010')
        self.assertIsInstance(replicated, VerilogBits)

    def test_equality(self):
        """Test the __eq__ method."""
        v1 = VerilogBits('0b101')
        v2 = VerilogBits('0b101')
        v3 = VerilogBits('0b000')
        self.assertEqual(v1, v2)
        self.assertNotEqual(v1, v3)
        # Test against other types
        self.assertNotEqual(v1, '0b101')
        self.assertNotEqual(v1, 5)

    def test_slicing_error_handling(self):
        """Test error handling for invalid slicing."""
        v = VerilogBits(length=8)
        with self.assertRaisesRegex(ValueError, r"LSB \(\d+\) cannot be greater than MSB \(\d+\)"):
            _ = v[4:5]
        with self.assertRaises(IndexError):
            _ = v[8:0]

    def test_unsupported_operations(self):
        """Test that unsupported operations raise TypeError."""
        v1 = VerilogBits('0b101')
        v2 = VerilogBits('0b010')

        with self.assertRaisesRegex(TypeError, "The '\\+' operator is disabled"): _ = v1 + v2
        with self.assertRaises(TypeError): _ = v1 > v2
        with self.assertRaises(TypeError): _ = v1 < v2
        with self.assertRaises(TypeError): _ = v1 - v2
        with self.assertRaises(TypeError): _ = v1 * 2
        with self.assertRaises(TypeError): _ = v1 & v2
        with self.assertRaises(TypeError): _ = ~v1
        with self.assertRaises(TypeError): _ = int(v1)
        with self.assertRaises(TypeError): _ = v1 + "1" # type: ignore

    def test_python_style_indexing(self):
        """Test standard Python integer indexing."""
        v = VerilogBits(value=170, length=8) # 0b10101010
        self.assertEqual(v[0].bin, '1')
        self.assertIsInstance(v[0], VerilogBits)
        self.assertEqual(v[7].bin, '0')

if __name__ == '__main__':
    unittest.main()
