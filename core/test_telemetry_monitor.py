import pytest
from core.telemetry_monitor import EmbeddingDriftDetector

def test_drift_detection_no_drift():
    detector = EmbeddingDriftDetector()
    
    # Baseline and current distributions are identical
    baseline = [[0.1, 0.2, 0.3]] * 10
    current = [[0.1, 0.2, 0.3]] * 10
    
    psi, ks, is_drift = detector.check_drift(baseline, current)
    assert psi < 0.1
    assert ks == 0.0
    assert not is_drift


def test_drift_detection_with_drift():
    detector = EmbeddingDriftDetector(psi_alert_threshold=0.25)
    
    # Baseline and current distributions stand far apart
    baseline = [[0.1, 0.1, 0.1]] * 20
    current = [[0.9, 0.9, 0.9]] * 20
    
    psi, ks, is_drift = detector.check_drift(baseline, current)
    assert psi > 0.25
    assert ks > 0.5
    assert is_drift
