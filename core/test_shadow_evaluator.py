import pytest
from core.shadow_evaluator import ShadowEvaluator

def test_shadow_evaluator_failure_mining_and_promotion():
    evaluator = ShadowEvaluator()
    
    # 1. Mine a failure -> Creates shadow guardrail
    g_id = evaluator.mine_failure("ZeroDivisionError: division by zero", "1/0")
    assert g_id in evaluator.candidate_guardrails
    assert evaluator.candidate_guardrails[g_id].is_shadow
    
    # 2. Evaluate -> Alert should match pattern but not throw exception (shadow mode)
    alerts = evaluator.evaluate_shadow_guardrails("Attempting computation: 1/0 inside loop")
    assert len(alerts) == 1
    assert "ZeroDivisionError" in alerts[0]
    assert evaluator.candidate_guardrails[g_id].hits == 1
    
    # 3. Promote -> Should fail if age < 72 hours
    promoted = evaluator.promote_guardrail(g_id, age_hours=12.0)
    assert not promoted
    assert evaluator.candidate_guardrails[g_id].is_shadow
    
    # Promote -> Should succeed if age >= 72 hours and no false positives
    promoted = evaluator.promote_guardrail(g_id, age_hours=75.0)
    assert promoted
    assert not evaluator.candidate_guardrails[g_id].is_shadow


def test_shadow_model_evaluation_and_promotion():
    evaluator = ShadowEvaluator()
    
    # Record semantic matches
    for _ in range(49999):
        evaluator.record_shadow_evaluation("llama-3-candidate", is_semantic_match=True)
    
    # After 49999 evaluations, stats should not be promoted
    assert not evaluator.shadow_model_stats["llama-3-candidate"].promoted
    
    # The 50,000th evaluation triggers check
    evaluator.record_shadow_evaluation("llama-3-candidate", is_semantic_match=True)
    assert evaluator.shadow_model_stats["llama-3-candidate"].promoted


def test_cold_path_distillation():
    evaluator = ShadowEvaluator()
    
    # Track reasoning pattern
    for _ in range(99):
        evaluator.track_cold_path("complex_tot_reasoning_sql")
        
    assert evaluator.distillation_backlog["complex_tot_reasoning_sql"] == 99
    
    # The 100th hit triggers recommendation alert
    evaluator.track_cold_path("complex_tot_reasoning_sql")
    assert evaluator.distillation_backlog["complex_tot_reasoning_sql"] == 100
