# -*- coding: utf-8 -*-
"""
UVM Lite Metrics - Unit Tests

Tests the MRED, NMED, SNR, PSNR calculation functions and the enhanced match feature.
This file is compatible with Python's unittest framework for automatic discovery.
"""

import unittest
import numpy as np
import logging
from veriflow import (
    MetricsCalculator, 
    DataMatcher,
    calculate_mred,
    calculate_nmed,
    calculate_snr,
    calculate_psnr,
    match_data,
    analyze_error_metrics
)

# Suppress logging output during tests to keep the test report clean
logging.basicConfig(level=logging.CRITICAL)

class TestMetrics(unittest.TestCase):

    def setUp(self):
        """Set up common data for tests."""
        np.random.seed(42)
        self.reference = np.random.randn(100) * 10 + 5
        noise = np.random.randn(100) * 0.1
        self.test = self.reference + noise
        self.calc = MetricsCalculator()
        self.matcher = DataMatcher(tolerance=0.2, max_mismatches=5)

    def test_basic_metrics_calculation(self):
        """Test the basic metrics calculation functions."""
        mred_val = calculate_mred(self.reference, self.test)
        nmed_val = calculate_nmed(self.reference, self.test)
        snr_val = calculate_snr(self.reference, self.test)
        psnr_val = calculate_psnr(self.reference, self.test)
        
        # Verify that the results are reasonable
        self.assertGreater(mred_val, 0, "MRED should be positive")
        self.assertGreater(nmed_val, 0, "NMED should be positive")
        self.assertGreater(snr_val, 0, "SNR should be positive")
        self.assertGreater(psnr_val, 0, "PSNR should be positive")

    def test_data_matching_functionality(self):
        """Test the data matching feature."""
        ref_match = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        test_match = np.array([1, 2, 3, 4, 5.1, 6, 7, 8, 9, 10.5])  # Two mismatches

        match_result = self.matcher.match(ref_match, test_match, show_mismatches=False)
        
        self.assertEqual(match_result['total_elements'], 10)
        self.assertEqual(match_result['mismatch_count'], 2)
        self.assertFalse(match_result['is_match'])

    def test_error_analysis_function(self):
        """Test the comprehensive error analysis function."""
        analysis_result = analyze_error_metrics(
            self.reference, 
            self.test, 
            max_value=np.max(np.abs(self.reference))
        )
        
        summary = analysis_result['summary']
        self.assertGreater(summary['snr_db'], 0)
        self.assertGreater(summary['psnr_db'], 0)
        self.assertGreater(summary['mred'], 0)
        self.assertGreater(summary['nmed'], 0)
        self.assertGreater(summary['mean_error'], 0)
        self.assertGreater(summary['max_error'], 0)

    def test_multidimensional_data_handling(self):
        """Test that metrics can handle multi-dimensional data."""
        ref_2d = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=float)
        test_2d = np.array([[1, 2, 3], [4, 5.1, 6], [7, 8, 9.2]], dtype=float)
        
        metrics_2d = self.calc.calculate_all_metrics(ref_2d, test_2d)
        # Use a smaller tolerance for this specific test to detect the mismatches
        matcher_strict = DataMatcher(tolerance=1e-5, max_mismatches=5)
        match_result_2d = matcher_strict.match(ref_2d, test_2d, show_mismatches=False)
        
        self.assertGreater(metrics_2d['mred'], 0)
        self.assertGreater(metrics_2d['snr'], 0)
        self.assertEqual(match_result_2d['mismatch_count'], 2)

    def test_error_handling_for_invalid_input(self):
        """Test error handling for mismatched shapes and empty inputs."""
        # Test for mismatched shapes
        ref_mismatch = np.array([1, 2, 3])
        test_mismatch = np.array([1, 2])
        # Match the English error message for mismatched shapes
        with self.assertRaisesRegex(ValueError, "shapes do not match"):
            self.calc.mred(ref_mismatch, test_mismatch)
            
        # Test for empty arrays
        ref_empty = np.array([])
        test_empty = np.array([])
        # Match the English error message for empty data
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            self.calc.mred(ref_empty, test_empty)

if __name__ == "__main__":
    unittest.main()
