"""
VeriFlow Metrics Module

Provides common metrics for digital signal processing and verification:
- MRED (Maximum Relative Error Distance)
- NMED (Normalized Mean Error Distance)
- SNR (Signal-to-Noise Ratio)
- PSNR (Peak Signal-to-Noise Ratio)
- Enhanced match function to list all mismatches.
"""

import numpy as np
import logging
from typing import Union, List, Tuple, Optional, Dict, Any
from .verilogger import logger as verilogger

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Digital Signal Processing Metrics Calculator
    
    Provides common metrics such as MRED, NMED, SNR, and PSNR.
    """
    
    def __init__(self, tolerance: float = 1e-10):
        """
        Initializes the metrics calculator.
        
        :param tolerance: Tolerance for numerical comparisons to avoid division by zero.
        """
        self.tolerance = tolerance
    
    def _validate_inputs(self, reference: np.ndarray, test: np.ndarray) -> None:
        """
        Validates the input data.
        
        :param reference: Reference data
        :param test: Test data
        :raises ValueError: If input data is invalid.
        """
        if not isinstance(reference, np.ndarray) or not isinstance(test, np.ndarray):
            raise ValueError("Input data must be numpy arrays.")
        
        if reference.shape != test.shape:
            raise ValueError(f"Reference and test data shapes do not match: {reference.shape} vs {test.shape}")
        
        if reference.size == 0:
            raise ValueError("Input data cannot be empty.")
    
    def _safe_divide(self, numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
        """
        Safe division to avoid division-by-zero errors.
        
        :param numerator: Numerator
        :param denominator: Denominator
        :return: Result of the division.
        """
        denom = denominator.copy()
        denom[np.abs(denom) < self.tolerance] = self.tolerance
        return numerator / denom
    
    def mred(self, reference: np.ndarray, test: np.ndarray) -> float:
        """
        Calculates the Maximum Relative Error Distance (MRED).
        
        MRED = max(|reference - test| / |reference|)
        
        :param reference: Reference data
        :param test: Test data
        :return: MRED value.
        """
        self._validate_inputs(reference, test)
        
        error = np.abs(reference - test)
        relative_error = self._safe_divide(error, np.abs(reference))
        
        mred_value = np.max(relative_error)
        logger.info(f"MRED = {mred_value:.6e}")
        return mred_value
    
    def nmed(self, reference: np.ndarray, test: np.ndarray) -> float:
        """
        Calculates the Normalized Mean Error Distance (NMED).
        
        NMED = mean(|reference - test|) / mean(|reference|)
        
        :param reference: Reference data
        :param test: Test data
        :return: NMED value.
        """
        self._validate_inputs(reference, test)
        
        error = np.abs(reference - test)
        mean_error = np.mean(error)
        mean_reference = np.mean(np.abs(reference))
        
        # Handle case where mean reference is close to zero
        if mean_reference < self.tolerance:
            mean_reference = self.tolerance
        
        nmed_value = mean_error / mean_reference
        logger.info(f"NMED = {nmed_value:.6e}")
        return float(nmed_value)
    
    def snr(self, reference: np.ndarray, test: np.ndarray) -> float:
        """
        Calculates the Signal-to-Noise Ratio (SNR).
        
        SNR = 10 * log10(mean(reference^2) / mean((reference - test)^2))
        
        :param reference: Reference data
        :param test: Test data
        :return: SNR value in dB.
        """
        self._validate_inputs(reference, test)
        
        signal_power = np.mean(reference ** 2)
        noise_power = np.mean((reference - test) ** 2)
        
        if noise_power < self.tolerance:
            logger.warning("Noise power is close to zero, SNR may be inaccurate.")
            noise_power = self.tolerance
        
        snr_value = 10 * np.log10(signal_power / noise_power)
        logger.info(f"SNR = {snr_value:.2f} dB")
        return snr_value
    
    def psnr(self, reference: np.ndarray, test: np.ndarray, 
             max_value: Optional[float] = None) -> float:
        """
        Calculates the Peak Signal-to-Noise Ratio (PSNR).
        
        PSNR = 20 * log10(max_value / sqrt(mean((reference - test)^2)))
        
        :param reference: Reference data
        :param test: Test data
        :param max_value: The maximum possible pixel value of the signal. If None, it's taken from the reference data.
        :return: PSNR value in dB.
        """
        self._validate_inputs(reference, test)
        
        if max_value is None:
            max_value = np.max(np.abs(reference))
        
        mse = np.mean((reference - test) ** 2)
        
        if mse < self.tolerance:
            logger.warning("Mean Squared Error is close to zero, PSNR may be inaccurate.")
            mse = self.tolerance
        
        psnr_value = 20 * np.log10(max_value / np.sqrt(mse))
        logger.info(f"PSNR = {psnr_value:.2f} dB")
        return psnr_value
    
    def calculate_all_metrics(self, reference: np.ndarray, test: np.ndarray,
                            max_value: Optional[float] = None) -> Dict[str, float]:
        """
        Calculates all available metrics.
        
        :param reference: Reference data
        :param test: Test data
        :param max_value: Max value for PSNR calculation.
        :return: A dictionary containing all metric values.
        """
        verilogger.title("Calculating Signal Quality Metrics")
        
        metrics = {
            'mred': self.mred(reference, test),
            'nmed': self.nmed(reference, test),
            'snr': self.snr(reference, test),
            'psnr': self.psnr(reference, test, max_value)
        }
        
        verilogger.title("Metrics Summary")
        for metric_name, value in metrics.items():
            verilogger.info(f"{metric_name.upper()}: {value:.6e}" if metric_name in ['mred', 'nmed'] else f"{metric_name.upper()}: {value:.2f} dB")
        
        return metrics


class DataMatcher:
    """
    Data Matcher
    
    Provides enhanced data comparison, with the ability to list all mismatch locations.
    """
    
    def __init__(self, tolerance: float = 1e-10, max_mismatches: int = 100):
        """
        Initializes the data matcher.
        
        :param tolerance: Tolerance for numerical comparison.
        :param max_mismatches: Maximum number of mismatches to display.
        """
        self.tolerance = tolerance
        self.max_mismatches = max_mismatches
    
    def _validate_inputs(self, reference: np.ndarray, test: np.ndarray) -> None:
        """
        Validates the input data.
        
        :param reference: Reference data
        :param test: Test data
        :raises ValueError: If input data is invalid.
        """
        if not isinstance(reference, np.ndarray) or not isinstance(test, np.ndarray):
            raise ValueError("Input data must be numpy arrays.")
        
        if reference.shape != test.shape:
            raise ValueError(f"Reference and test data shapes do not match: {reference.shape} vs {test.shape}")
        
        if reference.size == 0:
            raise ValueError("Input data cannot be empty.")
    
    def match(self, reference: np.ndarray, test: np.ndarray, 
              show_mismatches: bool = True) -> Dict[str, Any]:
        """
        Compares two arrays and returns detailed matching results.
        
        :param reference: Reference data
        :param test: Test data
        :param show_mismatches: Whether to display details of mismatches.
        :return: A dictionary with matching results.
        """
        self._validate_inputs(reference, test)
        
        verilogger.title("Data Matching Analysis")
        
        # Calculate mismatch positions
        if reference.dtype.kind in 'fc':  # float or complex
            mismatch_mask = np.abs(reference - test) > self.tolerance
        else:  # integer or boolean
            mismatch_mask = reference != test
        
        total_elements = reference.size
        mismatch_count = np.sum(mismatch_mask)
        match_count = total_elements - mismatch_count
        match_percentage = (match_count / total_elements) * 100
        
        result = {
            'total_elements': total_elements,
            'match_count': match_count,
            'mismatch_count': mismatch_count,
            'match_percentage': match_percentage,
            'is_match': mismatch_count == 0,
            'mismatch_positions': [],
            'mismatch_details': []
        }
        
        verilogger.info(f"Total Elements: {total_elements}")
        verilogger.info(f"Matches: {match_count}")
        verilogger.info(f"Mismatches: {mismatch_count}")
        verilogger.info(f"Match Rate: {match_percentage:.2f}%")
        verilogger.info(f"Match Status: {'✅ Perfect Match' if result['is_match'] else '❌ Mismatches Found'}")
        
        if mismatch_count > 0 and show_mismatches:
            self._show_mismatch_details(reference, test, mismatch_mask, result)
        
        return result
    
    def _show_mismatch_details(self, reference: np.ndarray, test: np.ndarray, 
                              mismatch_mask: np.ndarray, result: Dict[str, Any]) -> None:
        """
        Displays the details of the mismatches.
        
        :param reference: Reference data
        :param test: Test data
        :param mismatch_mask: Mismatch mask
        :param result: Result dictionary to populate.
        """
        mismatch_indices = np.where(mismatch_mask)
        
        verilogger.title("Mismatch Details")
        
        # Safely get the number of mismatches
        if len(mismatch_indices) > 0 and len(mismatch_indices[0]) > 0:
            num_mismatches = len(mismatch_indices[0])
            verilogger.info(f"Showing first {min(self.max_mismatches, num_mismatches)} mismatches:")
            
            # Handle multi-dimensional arrays
            if len(mismatch_indices) > 1:
                # Multi-dimensional array
                for i in range(min(self.max_mismatches, num_mismatches)):
                    pos = tuple(idx[i] for idx in mismatch_indices)
                    ref_val = reference[pos]
                    test_val = test[pos]
                    error = abs(ref_val - test_val) if hasattr(ref_val, '__sub__') else 'N/A'
                    
                    result['mismatch_positions'].append(pos)
                    result['mismatch_details'].append({
                        'position': pos,
                        'reference': ref_val,
                        'test': test_val,
                        'error': error
                    })
                    
                    verilogger.info(f"  Position {pos}: Reference={ref_val}, Test={test_val}, Error={error}")
            else:
                # One-dimensional array
                for i in range(min(self.max_mismatches, num_mismatches)):
                    pos = mismatch_indices[0][i]
                    ref_val = reference[pos]
                    test_val = test[pos]
                    error = abs(ref_val - test_val) if hasattr(ref_val, '__sub__') else 'N/A'
                    
                    result['mismatch_positions'].append(pos)
                    result['mismatch_details'].append({
                        'position': pos,
                        'reference': ref_val,
                        'test': test_val,
                        'error': error
                    })
                    
                    verilogger.info(f"  Position {pos}: Reference={ref_val}, Test={test_val}, Error={error}")
            
            if num_mismatches > self.max_mismatches:
                verilogger.info(f"  ... and {num_mismatches - self.max_mismatches} more mismatches not shown.")
        else:
            verilogger.info("No mismatch positions found.")
    



# --- Convenience Functions ---

def calculate_mred(reference: np.ndarray, test: np.ndarray, tolerance: float = 1e-10) -> float:
    """Convenience function to calculate MRED."""
    calc = MetricsCalculator(tolerance)
    return calc.mred(reference, test)


def calculate_nmed(reference: np.ndarray, test: np.ndarray, tolerance: float = 1e-10) -> float:
    """Convenience function to calculate NMED."""
    calc = MetricsCalculator(tolerance)
    return calc.nmed(reference, test)


def calculate_snr(reference: np.ndarray, test: np.ndarray, tolerance: float = 1e-10) -> float:
    """Convenience function to calculate SNR."""
    calc = MetricsCalculator(tolerance)
    return calc.snr(reference, test)


def calculate_psnr(reference: np.ndarray, test: np.ndarray, 
                  max_value: Optional[float] = None, tolerance: float = 1e-10) -> float:
    """Convenience function to calculate PSNR."""
    calc = MetricsCalculator(tolerance)
    return calc.psnr(reference, test, max_value)


def match_data(reference: np.ndarray, test: np.ndarray, 
               tolerance: float = 1e-10, max_mismatches: int = 100, show_mismatches: bool = True) -> Dict[str, Any]:
    """Convenience function for data matching."""
    matcher = DataMatcher(tolerance, max_mismatches)
    return matcher.match(reference, test, show_mismatches=show_mismatches)


def analyze_error_metrics(reference: np.ndarray, test: np.ndarray,
                         max_value: Optional[float] = None, tolerance: float = 1e-10) -> Dict[str, Any]:
    """
    Convenience function for a comprehensive error metrics analysis.
    
    Focuses on error analysis, does not include matching.
    
    :param reference: Reference data
    :param test: Test data
    :param max_value: Max value for PSNR calculation.
    :param tolerance: Tolerance for numerical comparison.
    :return: A dictionary with all error metrics analysis.
    """
    verilogger.title("Comprehensive Error Metrics Analysis")
    
    # Calculate all error metrics
    calc = MetricsCalculator(tolerance)
    metrics = calc.calculate_all_metrics(reference, test, max_value)
    
    # Calculate additional statistics
    error = np.abs(reference - test)
    error_stats = {
        'mean_error': float(np.mean(error)),
        'std_error': float(np.std(error)),
        'max_error': float(np.max(error)),
        'min_error': float(np.min(error)),
        'median_error': float(np.median(error))
    }
    
    # Combine results
    analysis_result = {
        'metrics': metrics,
        'error_statistics': error_stats,
        'summary': {
            'snr_db': metrics['snr'],
            'psnr_db': metrics['psnr'],
            'mred': metrics['mred'],
            'nmed': metrics['nmed'],
            'mean_error': error_stats['mean_error'],
            'max_error': error_stats['max_error']
        }
    }
    
    verilogger.title("Error Analysis Summary")
    verilogger.info(f"Signal-to-Noise Ratio: {analysis_result['summary']['snr_db']:.2f} dB")
    verilogger.info(f"Peak Signal-to-Noise Ratio: {analysis_result['summary']['psnr_db']:.2f} dB")
    verilogger.info(f"Max Relative Error Distance: {analysis_result['summary']['mred']:.6e}")
    verilogger.info(f"Normalized Mean Error Distance: {analysis_result['summary']['nmed']:.6e}")
    verilogger.info(f"Mean Absolute Error: {analysis_result['summary']['mean_error']:.6e}")
    verilogger.info(f"Max Absolute Error: {analysis_result['summary']['max_error']:.6e}")
    
    return analysis_result
