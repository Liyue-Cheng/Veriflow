# -*- coding: utf-8 -*-
"""
Test script for veriflow.mem_tools, refactored for unittest discovery.

This test verifies the functionality of read and write operations for both
hexadecimal and binary memory files.
"""

import os
import unittest
import numpy as np
from veriflow.verilog_bits import VerilogBits
from veriflow.mem_tools import write_memh, read_memh, write_memb, read_memb

class TestMemTools(unittest.TestCase):

    def setUp(self):
        """
        This method is called before each test function.
        It sets up the environment for the test.
        """
        self.work_dir = "temp_test_outputs"
        os.makedirs(self.work_dir, exist_ok=True)
        
        # --- Generate common test data ---
        self.num_samples = 256
        self.original_data_a = np.random.randint(0, 2**16, size=self.num_samples, dtype=np.uint16)
        self.original_data_b = np.random.randint(0, 2**16, size=self.num_samples, dtype=np.uint16)
        
        vectors_a = [VerilogBits(int(x), length=16) for x in self.original_data_a]
        vectors_b = [VerilogBits(int(x), length=16) for x in self.original_data_b]
        
        # Use the new VerilogBits.concat() method instead of the disabled '+' operator
        self.concatenated_vectors = [VerilogBits.concat(vb, va) for va, vb in zip(vectors_a, vectors_b)]
        
        self.hex_file_path = os.path.join(self.work_dir, "test_data.hex")
        self.bin_file_path = os.path.join(self.work_dir, "test_data.bin")

    def tearDown(self):
        """
        This method is called after each test function.
        It cleans up any files created during the test.
        """
        if os.path.exists(self.hex_file_path):
            os.remove(self.hex_file_path)
        if os.path.exists(self.bin_file_path):
            os.remove(self.bin_file_path)
        if os.path.exists(self.work_dir) and not os.listdir(self.work_dir):
            os.rmdir(self.work_dir)

    def _verify_data(self, read_vectors, orig_a, orig_b, format_name):
        """Helper method to unpack and verify data."""
        self.assertEqual(len(read_vectors), len(self.concatenated_vectors),
                         f"{format_name} Read Error: Mismatch in number of vectors read.")
        
        unpacked_a = np.zeros_like(orig_a)
        unpacked_b = np.zeros_like(orig_b)

        for i, vec in enumerate(read_vectors):
            # Unpack: vec[15:0] is A, vec[31:16] is B
            unpacked_a[i] = vec[15:0].uint
            unpacked_b[i] = vec[31:16].uint

        # Use unittest assertions for verification
        self.assertTrue(np.array_equal(orig_a, unpacked_a),
                        f"{format_name} Verification Failed for Data A!")
        self.assertTrue(np.array_equal(orig_b, unpacked_b),
                        f"{format_name} Verification Failed for Data B!")

    def test_hex_format(self):
        """
        Tests writing and reading in hexadecimal format ($readmemh/$writememh).
        """
        # --- Write to file ---
        write_memh(self.hex_file_path, self.concatenated_vectors, words_per_line=4)
        self.assertTrue(os.path.exists(self.hex_file_path))
        
        # --- Read from file ---
        read_vectors = read_memh(self.hex_file_path, word_width=32)
        
        # --- Verify ---
        self._verify_data(read_vectors, self.original_data_a, self.original_data_b, "HEX")

    def test_bin_format(self):
        """
        Tests writing and reading in binary format ($readmemb/$writememb).
        """
        # --- Write to file ---
        write_memb(self.bin_file_path, self.concatenated_vectors, words_per_line=1)
        self.assertTrue(os.path.exists(self.bin_file_path))

        # --- Read from file ---
        read_vectors = read_memb(self.bin_file_path, word_width=32)

        # --- Verify ---
        self._verify_data(read_vectors, self.original_data_a, self.original_data_b, "BIN")

if __name__ == "__main__":
    # This allows the test to be run standalone as well as by the test runner
    unittest.main()
