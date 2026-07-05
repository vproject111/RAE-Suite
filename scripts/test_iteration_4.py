import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from core.autonomy_kernel import AutonomyKernel
from rae_contracts import ExecutionStatus, QualityStatus

class MockBridge:
    def log_decision(self, action, reasoning, payload):
        print(f"🌉 [Bridge] {action}: {reasoning}")
    def save_event(self, text, layer="episodic"):
        print(f"📝 [Memory] {text}")

async def test_iteration_4():
    bridge = MockBridge()
    kernel = AutonomyKernel(bridge=bridge, repo_root=".")
    
    print("\n--- Case 1: Test Weakening Detected (QUARANTINE) ---")
    orig_test = "def test_math():\n    assert 1 + 1 == 2\n    assert 2 + 2 == 4"
    mod_test = "def test_math():\n    assert 1 + 1 == 2\n    # Deleted one assert"
    
    receipt1 = await kernel.execute_task(
        goal_id="g1", task_id="t1", intent="Refactor tests", 
        payload={"original_test": orig_test, "modified_test": mod_test}
    )
    print(f"Result: {receipt1.execution_status}, Quality: {receipt1.quality_status}")

    print("\n--- Case 2: Coverage Regression Detected (REJECT) ---")
    receipt2 = await kernel.execute_task(
        goal_id="g2", task_id="t2", intent="Update logic", 
        payload={
            "metrics": {
                "tests_passed": True, 
                "coverage_before": 90.0, 
                "coverage_after": 85.0 # Regression!
            }
        }
    )
    print(f"Result: {receipt2.execution_status}, Quality: {receipt2.quality_status}")

    print("\n--- Case 3: Quality PASS ---")
    receipt3 = await kernel.execute_task(
        goal_id="g3", task_id="t3", intent="Clean up", 
        payload={
            "metrics": {
                "tests_passed": True, 
                "coverage_before": 80.0, 
                "coverage_after": 80.5
            }
        }
    )
    print(f"Result: {receipt3.execution_status}, Quality: {receipt3.quality_status}")

if __name__ == "__main__":
    try:
        asyncio.run(test_iteration_4())
    except Exception as e:
        print(f"❌ Test failed: {e}")
