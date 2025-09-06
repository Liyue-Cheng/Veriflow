# -*- coding: utf-8 -*-
"""
Verilogger Comprehensive Test Suite
===================================

This module provides complete test coverage for the Verilogger class,
including all logging functionality, table generation, thread safety,
and optimization features.

Test Coverage:
- Basic logging functionality (debug, info, success, warning, error, critical)
- Plain text writing capabilities (write, writeln)
- EDA-style reporting (title, separator, table generation)
- File output management and idempotency
- Thread safety for multi-threaded environments
- Error/warning counter accuracy
- Exception catching decorator
- Summary report generation
"""

import unittest
import os
import sys
import threading
import time
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor
from io import StringIO

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from veriflow.verilogger import Verilogger


class TestVeriloggerBasic(unittest.TestCase):
    """Test basic logging functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.logger = Verilogger()
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_logging_methods_exist(self):
        """Test that all logging methods exist and are callable"""
        methods = ['debug', 'info', 'success', 'warning', 'error', 'critical']
        for method in methods:
            self.assertTrue(hasattr(self.logger, method))
            self.assertTrue(callable(getattr(self.logger, method)))
    
    def test_counter_increment(self):
        """Test that error and warning counters increment correctly"""
        initial_errors = self.logger.get_error_count()
        initial_warnings = self.logger.get_warning_count()
        
        self.logger.error("Test error")
        self.logger.warning("Test warning")
        self.logger.critical("Test critical")
        
        self.assertEqual(self.logger.get_error_count(), initial_errors + 2)  # error + critical
        self.assertEqual(self.logger.get_warning_count(), initial_warnings + 1)
    
    def test_plain_text_writing(self):
        """Test plain text writing functionality"""
        # Test that write methods exist and are callable
        self.assertTrue(hasattr(self.logger, 'write'))
        self.assertTrue(hasattr(self.logger, 'writeln'))
        self.assertTrue(callable(self.logger.write))
        self.assertTrue(callable(self.logger.writeln))
        
        # Test that methods execute without error
        self.logger.write("Test message")
        self.logger.writeln("Test message with newline")
        self.logger.writeln()  # Empty line


class TestVeriloggerEDAReporting(unittest.TestCase):
    """Test EDA-style reporting functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.logger = Verilogger()
    
    def test_title_generation(self):
        """Test title generation with different parameters"""
        # Test basic title
        self.logger.title("Test Title")
        
        # Test title with custom width and character
        self.logger.title("Custom Title", width=50, char='-')
    
    def test_subtitle_generation(self):
        """Test subtitle generation with different parameters"""
        # Test basic subtitle
        self.logger.subtitle("Test Subtitle")
        
        # Test subtitle with custom width and character
        self.logger.subtitle("Custom Subtitle", width=60, char='*')
        
        # Test subtitle with different characters
        self.logger.subtitle("Dotted Subtitle", char='.')
        self.logger.subtitle("Equal Subtitle", char='=')
        self.logger.subtitle("Hash Subtitle", char='#')
    
    def test_separator_generation(self):
        """Test separator generation"""
        self.logger.separator()
        self.logger.separator('-', 60)
        self.logger.separator('=', 40)
    
    def test_table_generation(self):
        """Test table generation with various content types"""
        # Test basic ASCII table
        headers = ["Module", "Status", "Time"]
        rows = [
            ["cpu_core", "PASS", "1.2s"],
            ["memory_ctrl", "FAIL", "2.5s"],
            ["uart", "PASS", "0.8s"]
        ]
        self.logger.table(headers, rows)
        
        # Test table with different column widths
        headers2 = ["ID", "Very Long Column Header", "Short", "Description"]
        rows2 = [
            ["1", "short content", "A", "Brief description"],
            ["22", "much longer content here", "BB", "Much longer description text"],
            ["333", "medium", "CCC", "Normal description"]
        ]
        self.logger.table(headers2, rows2)
        
        # Test empty table
        self.logger.table([], [])
        self.logger.table(["Header"], [])


class TestVeriloggerFileOperations(unittest.TestCase):
    """Test file output functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.logger = Verilogger()
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_file_addition(self):
        """Test adding file output targets"""
        test_file = os.path.join(self.test_dir, "test_output.log")
        
        # Test file addition
        self.logger.add(test_file, mode='w')
        
        # Write some content
        self.logger.info("Test message to file")
        self.logger.write("Plain text to file\n")
        
        # Verify file was created and contains content
        self.assertTrue(os.path.exists(test_file))
        
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Test message to file", content)
            self.assertIn("Plain text to file", content)
    
    def test_add_idempotency(self):
        """Test that add() method is idempotent"""
        test_file = os.path.join(self.test_dir, "idempotent_test.log")
        
        # First addition should succeed
        self.logger.add(test_file, mode='w')
        initial_file_count = len(self.logger._output_files)
        
        # Second addition should be skipped with warning
        self.logger.add(test_file, mode='w')
        
        # File count should remain the same
        self.assertEqual(len(self.logger._output_files), initial_file_count)
        
        # File should be tracked as added
        self.assertIn(test_file, self.logger._added_files)
    
    def test_directory_auto_creation(self):
        """Test that add() method automatically creates directories"""
        # Create a nested directory path that doesn't exist
        nested_dir = os.path.join(self.test_dir, "nested", "deep", "path")
        test_file = os.path.join(nested_dir, "auto_created.log")
        
        # Verify the directory doesn't exist initially
        self.assertFalse(os.path.exists(nested_dir))
        
        # Add file - this should create the directory structure
        self.logger.add(test_file, mode='w')
        
        # Verify directory was created
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.isdir(nested_dir))
        
        # Verify file was created
        self.assertTrue(os.path.exists(test_file))
        
        # Write some content to verify file is functional
        self.logger.info("Test message to auto-created directory")
        self.logger.write("Plain text to auto-created file\n")
        
        # Verify content was written
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Test message to auto-created directory", content)
            self.assertIn("Plain text to auto-created file", content)
    
    def test_directory_creation_error_handling(self):
        """Test error handling when directory creation fails"""
        # Create a path that would be invalid on most systems
        invalid_path = "C:\\invalid\\path\\with\\reserved\\characters\\<test>.log"
        
        # This should not raise an exception, but should log an error
        self.logger.add(invalid_path, mode='w')
        
        # The file should not be added to the output files
        self.assertNotIn(invalid_path, self.logger._added_files)
        self.assertEqual(len(self.logger._output_files), 0)


class TestVeriloggerThreadSafety(unittest.TestCase):
    """Test thread safety of Verilogger operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.logger = Verilogger()
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_concurrent_counter_updates(self):
        """Test thread safety of error/warning counters"""
        num_threads = 3
        operations_per_thread = 10
        
        def counter_worker(thread_id):
            """Worker that generates errors and warnings"""
            for i in range(operations_per_thread):
                if i % 2 == 0:
                    self.logger.error(f"Error from thread {thread_id}, op {i}")
                else:
                    self.logger.warning(f"Warning from thread {thread_id}, op {i}")
        
        # Get initial counts
        initial_errors = self.logger.get_error_count()
        initial_warnings = self.logger.get_warning_count()
        
        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(counter_worker, i) for i in range(num_threads)]
            for future in futures:
                future.result()
        
        # Calculate expected counts
        expected_errors = initial_errors + (num_threads * (operations_per_thread // 2 + operations_per_thread % 2))
        expected_warnings = initial_warnings + (num_threads * (operations_per_thread // 2))
        
        # Verify counts are correct
        self.assertEqual(self.logger.get_error_count(), expected_errors)
        self.assertEqual(self.logger.get_warning_count(), expected_warnings)
    
    def test_concurrent_write_operations(self):
        """Test thread safety of write operations"""
        num_threads = 5
        messages_per_thread = 5
        
        def write_worker(thread_id):
            """Worker that performs write operations"""
            for i in range(messages_per_thread):
                self.logger.info(f"Thread-{thread_id}: Message {i+1}")
                self.logger.write(f"Plain text from Thread-{thread_id}, message {i+1}\n")
        
        # Run concurrent write operations
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(write_worker, i) for i in range(num_threads)]
            for future in futures:
                future.result()
        
        # If we reach here without deadlock or exception, test passes
        self.assertTrue(True)
    
    def test_concurrent_file_operations(self):
        """Test concurrent file addition and writing"""
        num_workers = 3
        
        def file_worker(worker_id):
            """Worker that adds a file and writes to it"""
            test_file = os.path.join(self.test_dir, f"concurrent_{worker_id}.log")
            self.logger.add(test_file, mode='w')
            
            for i in range(3):
                self.logger.write(f"Content from worker {worker_id}, line {i+1}\n")
        
        # Run concurrent file operations
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(file_worker, i) for i in range(num_workers)]
            for future in futures:
                future.result()
        
        # Verify all files were created
        for i in range(num_workers):
            test_file = os.path.join(self.test_dir, f"concurrent_{i}.log")
            self.assertTrue(os.path.exists(test_file))


class TestVeriloggerAdvancedFeatures(unittest.TestCase):
    """Test advanced Verilogger features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.logger = Verilogger()
    
    def test_exception_catching_decorator(self):
        """Test the exception catching decorator"""
        caught_exception = False
        
        @self.logger.catch(reraise=False)
        def failing_function():
            raise ValueError("Test exception")
        
        # This should not raise an exception
        result = failing_function()
        self.assertIsNone(result)  # Function should return None when exception is caught
    
    def test_exception_catching_with_reraise(self):
        """Test exception catching decorator with reraise=True"""
        @self.logger.catch(reraise=True)
        def failing_function():
            raise ValueError("Test exception")
        
        # This should raise the exception
        with self.assertRaises(ValueError):
            failing_function()
    
    def test_summary_generation(self):
        """Test summary report generation"""
        # Generate some errors and warnings
        self.logger.error("Test error 1")
        self.logger.error("Test error 2")
        self.logger.warning("Test warning 1")
        
        # Test that summary can be called without error
        self.logger.summary()
    
    def test_counter_getters_thread_safety(self):
        """Test that counter getters are thread-safe"""
        def counter_reader():
            """Worker that reads counters"""
            error_count = self.logger.get_error_count()
            warning_count = self.logger.get_warning_count()
            return error_count, warning_count
        
        def counter_modifier():
            """Worker that modifies counters"""
            self.logger.error("Concurrent error")
            self.logger.warning("Concurrent warning")
        
        # Run concurrent read and modify operations
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit multiple readers and modifiers
            futures = []
            for _ in range(5):
                futures.append(executor.submit(counter_reader))
                futures.append(executor.submit(counter_modifier))
            
            # Wait for all to complete
            for future in futures:
                future.result()
        
        # Test passes if no deadlock or exception occurs
        self.assertTrue(True)


class TestVeriloggerIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.logger = Verilogger()
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_complete_verification_workflow(self):
        """Test a complete verification workflow simulation"""
        # Add file output
        log_file = os.path.join(self.test_dir, "verification.log")
        self.logger.add(log_file, mode='w')
        
        # Simulate verification process
        self.logger.title("FPGA Design Verification Report")
        
        # Test some modules
        modules = ["cpu_core", "memory_ctrl", "uart_tx", "interrupt_ctrl"]
        results = []
        
        for i, module in enumerate(modules):
            self.logger.info(f"[{i+1}/{len(modules)}] Verifying module: {module}")
            
            if module == "memory_ctrl":
                self.logger.warning(f"Module {module} has timing warnings")
                status = "WARNING"
            elif module == "interrupt_ctrl":
                self.logger.error(f"Module {module} verification failed")
                status = "FAIL"
            else:
                self.logger.success(f"Module {module} verification passed")
                status = "PASS"
            
            results.append([module, status, f"{1.0 + i * 0.5:.1f}s"])
        
        # Generate results table
        self.logger.separator()
        headers = ["Module", "Status", "Time"]
        self.logger.table(headers, results)
        
        # Generate summary
        self.logger.summary()
        
        # Verify file was created and contains expected content
        self.assertTrue(os.path.exists(log_file))
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for key elements
            self.assertIn("FPGA Design Verification Report", content)
            self.assertIn("cpu_core", content)
            self.assertIn("Execution Summary Report", content)
    
    def test_stress_test_with_file_output(self):
        """Stress test with high volume of operations and file output"""
        log_file = os.path.join(self.test_dir, "stress_test.log")
        self.logger.add(log_file, mode='w')
        
        # Generate a high volume of log messages
        for i in range(50):  # Reduced for faster test execution
            self.logger.info(f"Stress test message {i}")
            if i % 10 == 0:
                self.logger.warning(f"Stress warning {i//10}")
            if i % 20 == 0:
                self.logger.error(f"Stress error {i//20}")
        
        # Generate a table
        headers = ["Iteration", "Status", "Notes"]
        rows = [[str(i), "PASS" if i % 3 != 0 else "FAIL", f"Test {i}"] for i in range(20)]
        self.logger.table(headers, rows)
        
        # Verify counts are correct
        expected_warnings = 5  # 0, 10, 20, 30, 40
        expected_errors = 3    # 0, 20, 40
        
        self.assertEqual(self.logger.get_warning_count(), expected_warnings)
        self.assertEqual(self.logger.get_error_count(), expected_errors)
        
        # Verify file exists and has reasonable size
        self.assertTrue(os.path.exists(log_file))
        file_size = os.path.getsize(log_file)
        self.assertGreater(file_size, 1000)  # Should have substantial content


if __name__ == '__main__':
    # Create a test suite with all test classes
    test_classes = [
        TestVeriloggerBasic,
        TestVeriloggerEDAReporting,
        TestVeriloggerFileOperations,
        TestVeriloggerThreadSafety,
        TestVeriloggerAdvancedFeatures,
        TestVeriloggerIntegration
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1) 