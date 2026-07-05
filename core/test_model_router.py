import pytest
from core.model_router import ModelRouter
from rae_contracts import RiskClass

def test_token_budget_routing():
    router = ModelRouter()
    
    # R1 task -> should use local llama-3.1-8b
    model_r1 = router.route_task(RiskClass.R1)
    assert model_r1 == "llama-3.1-8b"
    assert router.registry[model_r1].is_local
    
    # R4 task -> should use local mixtral-8x7b
    model_r4 = router.route_task(RiskClass.R4)
    assert model_r4 == "mixtral-8x7b"
    assert router.registry[model_r4].is_local
    
    # R6 task -> should use gemini-1.5-pro (external API)
    model_r6 = router.route_task(RiskClass.R6)
    assert model_r6 == "gemini-1.5-pro"
    assert not router.registry[model_r6].is_local


def test_quality_tribunal_quorum_models():
    router = ModelRouter()
    
    # Tier 1: Partial Court (100% Local models)
    t1_models = router.get_tribunal_quorum_models(tier=1)
    assert len(t1_models) == 3
    for m in t1_models:
        assert router.registry[m].is_local

    # Tier 2: Appellate Court (100% Local strong models)
    t2_models = router.get_tribunal_quorum_models(tier=2)
    assert len(t2_models) == 3
    for m in t2_models:
        assert router.registry[m].is_local

    # Tier 3: Supreme Court (Advanced API-based models)
    t3_models = router.get_tribunal_quorum_models(tier=3)
    assert len(t3_models) == 3
    for m in t3_models:
        assert not router.registry[m].is_local
