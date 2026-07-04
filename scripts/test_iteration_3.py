import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from core.autonomy_kernel import AutonomyKernel
from rae_contracts import ExecutionStatus, RiskClass

class MockBridge:
    def log_decision(self, action, reasoning, payload):
        print(f"🌉 [Bridge] {action}: {reasoning}")
        if action == "phoenix_iteration_completed":
             print(f"   -> Phoenix Attempt {payload['attempt_no']}: {payload['final_decision']}")

    def save_event(self, text, layer="episodic"):
        print(f"📝 [Memory] {text}")

async def test_iteration_3():
    bridge = MockBridge()
    # Using current dir as repo_root for testing
    kernel = AutonomyKernel(bridge=bridge, repo_root=".")
    
    print("\n--- Testing Phoenix Repair Loop (R2) ---")
    # Intent contains "fix", should trigger Phoenix
    receipt = await kernel.execute_task(
        goal_id="g-phx", 
        task_id="t-phx", 
        intent="Fix regression in core/engine.py", 
        payload={"target_file": "core/engine.py"}
    )
    
    print(f"\nFinal Task Status: {receipt.execution_status}")
    print(f"Risk Class: {receipt.risk_class}")
    print(f"Transitions: {[t.to_state for t in receipt.state_transitions]}")

if __name__ == "__main__":
    try:
        asyncio.run(test_iteration_3())
    except Exception as e:
        print(f"❌ Test failed: {e}")
