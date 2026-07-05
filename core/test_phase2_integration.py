import pytest
from core.model_router import ModelRouter
from core.quality_tribunal import QualityTribunal
from core.semantic_cache import ProbabilisticSemanticCache
from core.speculative_executor import SpeculativeToolExecutor
from core.tool_gateway import ToolGateway
from core.shadow_evaluator import ShadowEvaluator
from rae_contracts import RiskClass

@pytest.mark.anyio
async def test_phase2_full_integration():
    # 1. Initialize router and quality tribunal
    router = ModelRouter()
    tribunal = QualityTribunal(router)
    
    # 2. Evaluate code with multi-model consensus
    code_diff = "def my_func():\n    pass"
    verdict = await tribunal.evaluate_code_change(code_diff, tier=1)
    assert verdict.decision == "APPROVE"
    
    # 3. Initialize semantic cache and query it
    cache = ProbabilisticSemanticCache(validation_probability=0.0)  # disable validation for simple check
    cache.set("Get active nodes", "Node 1 and Node 2", volatility_score=1.5, embedding=[1.0, 0.0])
    
    cached_val = cache.get("Get active nodes", [0.99, 0.01])
    assert cached_val == "Node 1 and Node 2"
    
    # 4. Speculative Tool Execution (Safe vs Unsafe parallel execution)
    gateway = ToolGateway(".")
    executor = SpeculativeToolExecutor(gateway)
    speculative_results = await executor.execute_speculatively(
        trace_id="speculative-integration-trace",
        commands=[["git", "status"], ["rm", "-rf", "/"]],
        risk_class=RiskClass.R0
    )
    assert "git status" in speculative_results
    assert "rm -rf /" not in speculative_results
    
    # 5. Shadow Evaluator (Failure Mining and Distillation check)
    shadow_eval = ShadowEvaluator()
    g_id = shadow_eval.mine_failure("RecursionError", "def recurse(): recurse()")
    assert shadow_eval.candidate_guardrails[g_id].is_shadow
    
    # Track distillation cold path
    shadow_eval.track_cold_path("complex_math_routing")
    assert shadow_eval.distillation_backlog["complex_math_routing"] == 1
