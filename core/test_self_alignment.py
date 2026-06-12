import pytest
from unittest.mock import MagicMock
from core.autonomy_kernel import AutonomyKernel
from rae_contracts import RiskClass, ExecutionStatus, QualityStatus, TaskState

class MockBridge:
    def log_decision(self, action, reasoning, payload):
        pass
    def save_event(self, text, layer="episodic"):
        pass

@pytest.mark.asyncio
async def test_constitutional_self_alignment_loop():
    bridge = MockBridge()
    kernel = AutonomyKernel(bridge=bridge, repo_root=".")
    
    # Payload with an absolute path in the patch code (violates C6)
    payload = {
        "original_test": "def test_f(): assert True",
        "modified_test": "def test_f(): assert True",
        "target_file": "main.py",
        "patch_code": "def process_data():\n    # Hardcoded absolute path\n    file_path = '/home/grzegorz-lesniowski/data.txt'\n    return open(file_path).read()",
        "metrics": {
            "tests_passed": True,
            "coverage_before": 80.0,
            "coverage_after": 80.0
        }
    }
    
    # Run task (R2 local modification)
    receipt = await kernel.execute_task(
        goal_id="g-align",
        task_id="t-align",
        intent="Modify file to parse data",
        payload=payload
    )
    
    # The task should complete successfully because the rewrite loop caught the absolute path
    # and autonomously aligned the patch (Phoenix mock succeeds on the 3rd attempt, which is what phoenix_engine triggers)
    assert receipt.execution_status == ExecutionStatus.SUCCESS
    assert receipt.quality_status == QualityStatus.ACCEPT
    
    # Let's verify that the transition log shows the rewrite was triggered
    transition_reasons = [t.reason for t in receipt.state_transitions if t.reason]
    assert any("Constitutional violation" in r and "Triggering alignment rewrite" in r for r in transition_reasons)
    assert any("Aligned Quality Gate result: QualityStatus.ACCEPT" in r or "Aligned Quality Gate result: ACCEPT" in r for r in transition_reasons)
