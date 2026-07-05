import pytest
from core.model_router import ModelRouter
from core.quality_tribunal import QualityTribunal

@pytest.mark.anyio
async def test_quality_tribunal_majority_approve():
    router = ModelRouter()
    tribunal = QualityTribunal(router)
    
    # Safe code change -> should be APPROVED by majority
    code_diff = "def calculate_sum(a, b):\n    return a + b"
    verdict = await tribunal.evaluate_code_change(code_diff, tier=1)
    
    assert verdict.decision == "APPROVE"
    assert len(verdict.votes) == 3
    # Check that at least 2 models voted APPROVE
    assert sum(1 for v in verdict.votes if v.vote == "APPROVE") >= 2


@pytest.mark.anyio
async def test_quality_tribunal_reject_violations():
    router = ModelRouter()
    tribunal = QualityTribunal(router)
    
    # Code with C3 violation (forbidden import) -> should be REJECTED by majority
    code_diff = "import sentence_transformers\ndef calculate_sum(a, b):\n    return a + b"
    verdict = await tribunal.evaluate_code_change(code_diff, tier=1)
    
    assert verdict.decision == "REJECT"
    # Check that at least 2 models voted REJECT
    assert sum(1 for v in verdict.votes if v.vote == "REJECT") >= 2
