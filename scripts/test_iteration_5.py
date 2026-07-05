import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add the project root to sys.path
sys.path.append(os.getcwd())

from core.autonomy_kernel import AutonomyKernel
from core.guardrail_manager import GuardrailManager
from rae_contracts import ExecutionStatus

class MockBridge:
    def log_decision(self, action, reasoning, payload):
        print(f"🌉 [Bridge] {action}: {reasoning}")
    def save_event(self, text, layer="episodic"):
        print(f"📝 [Memory] {text}")

async def test_iteration_5():
    bridge = MockBridge()
    kernel = AutonomyKernel(bridge=bridge, repo_root=".")
    
    print("\n--- Case 1: Context Trust-Score Evaluation ---")
    payload = {
        "historical_context": [
            {"id": "mem1", "layer": "semantic", "historical_success_rate": 0.9}, # Trusted
            {"id": "mem2", "layer": "working", "historical_success_rate": 0.2},  # Untrusted
            {"id": "mem3", "layer": "episodic", "quarantined": True}             # Poisoned
        ]
    }
    
    receipt = await kernel.execute_task(
        goal_id="g1", task_id="t1", intent="Analyze code", payload=payload
    )
    
    print(f"Filtered context size: {len(payload['historical_context'])}")
    for mem in payload['historical_context']:
        print(f" -> Trusted Mem: {mem['id']} (Score: {mem['trust_score']:.2f})")

    print("\n--- Case 2: Guardrail Lifecycle (RAE-Lab) ---")
    gm = kernel.guardrail_manager
    record = await gm.register_candidate("trace-1", "IF intent == 'steal' THEN BLOCK")
    print(f"Status 1: {record.lifecycle_state}")
    
    record = await gm.promote_to_shadow(record)
    print(f"Status 2: {record.lifecycle_state}")
    
    # Try to promote before 72h
    record = await gm.evaluate_promotion(record, {"fp_rate": 0.0, "logs_replayed": 100, "conflicts": 0})
    print(f"Status 3 (Early): {record.lifecycle_state} (Promoted: {record.promoted})")
    
    # Simulate time passing (mocking record created_at)
    record.created_at = datetime.now(timezone.utc) - timedelta(hours=73)
    record = await gm.evaluate_promotion(record, {"fp_rate": 0.0, "logs_replayed": 1000, "conflicts": 0})
    print(f"Status 4 (Mature): {record.lifecycle_state} (Promoted: {record.promoted})")

if __name__ == "__main__":
    try:
        asyncio.run(test_iteration_5())
    except Exception as e:
        print(f"❌ Test failed: {e}")
