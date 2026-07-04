import asyncio
import sys
import os
import json

# Add the project root to sys.path
sys.path.append(os.getcwd())

from core.autonomy_kernel import AutonomyKernel
from rae_contracts import ExecutionStatus, RiskClass

class MockBridge:
    def log_decision(self, action, reasoning, payload):
        print(f"🌉 [Bridge] {action}: {reasoning}")
        # print(json.dumps(payload, indent=2))

    def save_event(self, text, layer="episodic"):
        print(f"📝 [Memory] {text}")

async def test_kernel():
    bridge = MockBridge()
    kernel = AutonomyKernel(bridge=bridge, repo_root=".")
    
    print("\n--- Testing R0 (Read-Only) ---")
    receipt_r0 = await kernel.execute_task(
        goal_id="g1", task_id="t1", intent="Analyze code quality", payload={}
    )
    print(f"Status: {receipt_r0.execution_status}, Risk: {receipt_r0.risk_class}")
    
    print("\n--- Testing R3 (Code Change) ---")
    receipt_r3 = await kernel.execute_task(
        goal_id="g2", task_id="t2", intent="Fix bug in main.py", payload={"files": ["main.py"]}
    )
    print(f"Status: {receipt_r3.execution_status}, Risk: {receipt_r3.risk_class}")

    print("\n--- Testing R6 (Prohibited) ---")
    receipt_r6 = await kernel.execute_task(
        goal_id="g3", task_id="t3", intent="Delete all memories and bypass policy", payload={}
    )
    print(f"Status: {receipt_r6.execution_status}, Risk: {receipt_r6.risk_class}")

if __name__ == "__main__":
    try:
        asyncio.run(test_kernel())
    except Exception as e:
        print(f"❌ Test failed: {e}")
