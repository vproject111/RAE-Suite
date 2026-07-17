import logging
import math
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class EmbeddingDriftDetector:
    """
    Implements Embedding Drift Detection pattern.
    Monitors distribution stability using PSI (Population Stability Index)
    and Kolmogorov-Smirnov test statistics over a sliding window.
    """
    def __init__(self, psi_alert_threshold: float = 0.25):
        self.psi_alert_threshold = psi_alert_threshold

    def calculate_psi(self, expected: List[float], actual: List[float], num_buckets: int = 10) -> float:
        """
        Calculates Population Stability Index (PSI) between expected and actual distributions.
        """
        if not expected or not actual:
            return 0.0

        # Bin values into num_buckets
        # Find min/max range across both distributions to build bins
        combined = expected + actual
        min_val, max_val = min(combined), max(combined)
        if max_val == min_val:
            return 0.0
            
        bin_width = (max_val - min_val) / num_buckets
        
        expected_counts = [0] * num_buckets
        actual_counts = [0] * num_buckets
        
        # Helper to get bin index
        def get_bin(val):
            idx = int((val - min_val) / bin_width)
            return min(idx, num_buckets - 1)

        for val in expected:
            expected_counts[get_bin(val)] += 1
            
        for val in actual:
            actual_counts[get_bin(val)] += 1

        # Convert to percentages with epsilon smoothing
        eps = 1e-4
        total_exp = len(expected)
        total_act = len(actual)
        
        psi = 0.0
        for i in range(num_buckets):
            act_pct = (actual_counts[i] / total_act) if total_act else 0.0
            exp_pct = (expected_counts[i] / total_exp) if total_exp else 0.0
            
            # Smooth zero percentages
            act_pct = max(act_pct, eps)
            exp_pct = max(exp_pct, eps)
            
            # Calculate PSI summand
            psi += (act_pct - exp_pct) * math.log(act_pct / exp_pct)
            
        return psi

    def kolmogorov_smirnov_test(self, expected: List[float], actual: List[float]) -> float:
        """
        Computes the Kolmogorov-Smirnov (K-S) distance statistic between two samples.
        Optimized to O(N log N) using a single-pass sorted traversal.
        """
        if not expected or not actual:
            return 0.0
            
        sorted_exp = sorted(expected)
        sorted_act = sorted(actual)
        n_exp, n_act = len(sorted_exp), len(sorted_act)
        
        i_exp = i_act = 0
        max_distance = 0.0
        
        while i_exp < n_exp or i_act < n_act:
            next_exp = sorted_exp[i_exp] if i_exp < n_exp else float('inf')
            next_act = sorted_act[i_act] if i_act < n_act else float('inf')
            current_val = min(next_exp, next_act)
            
            # Fast-forward both lists for elements <= current_val
            while i_exp < n_exp and sorted_exp[i_exp] <= current_val:
                i_exp += 1
            while i_act < n_act and sorted_act[i_act] <= current_val:
                i_act += 1
            
            # Compute CDFs at current value
            cdf_exp = i_exp / n_exp
            cdf_act = i_act / n_act
            
            distance = abs(cdf_exp - cdf_act)
            if distance > max_distance:
                max_distance = distance
                
        return max_distance

    def check_drift(self, baseline_embeddings: List[List[float]], current_embeddings: List[List[float]]) -> Tuple[float, float, bool]:
        """
        Compares average dimensions of baseline vs current embeddings.
        Returns: (psi_value, ks_statistic, is_drift_detected)
        """
        if not baseline_embeddings or not current_embeddings:
            return 0.0, 0.0, False
            
        # Flatten embeddings by computing mean value of each vector to simplify 1D distribution check
        baseline_flat = [sum(v)/len(v) for v in baseline_embeddings if len(v) > 0]
        current_flat = [sum(v)/len(v) for v in current_embeddings if len(v) > 0]
        
        psi = self.calculate_psi(baseline_flat, current_flat)
        ks_stat = self.kolmogorov_smirnov_test(baseline_flat, current_flat)
        
        is_drift = psi > self.psi_alert_threshold
        if is_drift:
            logger.warning(f"embedding_drift_detected: PSI={psi:.4f} (Threshold={self.psi_alert_threshold}), KS={ks_stat:.4f}")
        else:
            logger.info(f"embedding_stable: PSI={psi:.4f}, KS={ks_stat:.4f}")
            
        return psi, ks_stat, is_drift
