# -*- coding: utf-8 -*-
"""
UVM Lite - Regression Test Runner
==================================

This script provides a centralized way to run all unit tests for the uvm_lite library.
It uses Python's `unittest` framework to automatically discover and execute all tests
located in the `uvm_lite/internal_test/` directory.

Why this is important:
----------------------
- **Quality Assurance**: Ensures that new changes do not break existing functionality.
- **Automation**: Allows for easy, one-click execution of the entire test suite.
- **Maintainability**: As new tests are added to the `internal_test` directory,
  this script will automatically include them without any modification.

How to run:
-----------
From the root directory of the project, simply execute:
$ python run_regression_tests.py

The script will discover all files matching the pattern 'test_*.py' inside the
`uvm_lite/internal_test` directory and run them.
"""

import unittest
import sys
import os

def run_tests():
    """
    Discovers and runs all tests under the 'uvm_lite/internal_test' directory.
    """
    # Define the directory where the tests are located.
    test_dir = os.path.join('veriflow', 'internal_test')
    
    # Check if the test directory exists
    if not os.path.isdir(test_dir):
        print(f"Error: Test directory not found at '{test_dir}'")
        print("Please ensure you are running this script from the project's root directory.")
        sys.exit(1)

    print("======================================================================")
    print("                 UVM Lite Regression Test Suite")
    print("======================================================================")
    print(f"Discovering tests in: '{test_dir}'\n")

    # Use unittest's default test loader to discover tests.
    # It will search for any file named 'test_*.py' in the specified directory.
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')

    # Check if any tests were found
    if suite.countTestCases() == 0:
        print("No tests found. Please check the test directory and file naming ('test_*.py').")
        sys.exit(1)
        
    print(f"Found {suite.countTestCases()} tests. Running now...\n")
    
    # Use TextTestRunner to run the tests.
    # verbosity=2 provides more detailed output for each test.
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n----------------------------------------------------------------------")
    print("Regression Test Summary:")
    
    # Check the result and set the exit code accordingly.
    # This is useful for CI/CD pipelines.
    if result.wasSuccessful():
        print("\n✅ PASSED: All tests completed successfully.")
        return 0  # Exit with success code
    else:
        print(f"\n❌ FAILED: {len(result.failures) + len(result.errors)} out of {suite.countTestCases()} tests failed.")
        return 1  # Exit with failure code

if __name__ == '__main__':
    # Run the test function and exit with the appropriate status code.
    exit_code = run_tests()
    sys.exit(exit_code)
