import pytest
from core.semantic_cache import ProbabilisticSemanticCache

def test_semantic_cache_hit_and_eviction():
    # Force validation probability to 1.0 to trigger mock validation
    cache = ProbabilisticSemanticCache(validation_probability=1.0)
    
    # Store standard queries
    cache.set("Get memory status", "Status is healthy", volatility_score=1.0, embedding=[1.0, 0.0, 0.0])
    cache.set("Retrieve active containers", "Containers running: 5", volatility_score=2.0, embedding=[0.0, 1.0, 0.0])
    
    # 1. Successful semantic hit (similarity ~1.0)
    resp = cache.get("Get memory status", [0.99, 0.01, 0.0])
    assert resp == "Status is healthy"
    
    # 2. Validation failure causing Semantic Neighborhood Eviction
    # "deprecated" keyword forces failure in _mock_validate_source
    cache.set("Get deprecated memory status", "Status is deprecated", volatility_score=1.0, embedding=[0.98, 0.02, 0.0])
    
    # Query matching the deprecated key, triggers eviction of its neighborhood ([1.0, 0.0, 0.0] style embeddings)
    resp = cache.get("Get deprecated memory status", [0.98, 0.02, 0.0])
    assert resp is None  # Validation failed, returned None
    
    # Verify neighborhood is evicted
    assert cache.get("Get memory status", [1.0, 0.0, 0.0]) is None  # Evicted!
    # But unrelated cache entry is still there
    assert cache.get("Retrieve active containers", [0.0, 1.0, 0.0]) == "Containers running: 5"
