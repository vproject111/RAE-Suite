import pytest
from unittest.mock import patch, MagicMock
from core.autonomy_kernel import AutonomyKernel
from rae_contracts import RiskClass, ExecutionStatus, QualityStatus, TaskState, VoteType

class MockBridge:
    def log_decision(self, action, reasoning, payload):
        pass
    def save_event(self, text, layer="episodic"):
        pass

@pytest.mark.asyncio
@patch("subprocess.run")
async def test_swarm_consensus_approve(mock_run):
    # Mock subprocess.run to simulate successful OpenClaw execution
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "OpenClaw mock run successful"
    mock_run.return_value = mock_proc

    bridge = MockBridge()
    kernel = AutonomyKernel(bridge=bridge, repo_root=".")
    
    # We want a task that triggers R4 (e.g. alembic migrate schema modification)
    payload = {
        "target_agent": "rae-openclaw", # Authorized for R4
        "metrics": {
            "tests_passed": True,
            "coverage_before": 80.0,
            "coverage_after": 80.0
        }
    }
    
    receipt = await kernel.execute_task(
        goal_id="g-swarm",
        task_id="t-swarm",
        intent="Run alembic migrate to modify database schema",
        payload=payload
    )
    
    # The swarm consensus should approve this since it uses Alembic
    assert receipt.execution_status == ExecutionStatus.SUCCESS
    assert "swarm_consensus_proposal" in payload
    assert payload["swarm_consensus_proposal"]["final_decision"] == VoteType.APPROVE

@pytest.mark.asyncio
@patch("subprocess.run")
async def test_swarm_consensus_reject_veto(mock_run):
    # Even if run is called (it shouldn't be, since we reject early), mock it
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_run.return_value = mock_proc

    bridge = MockBridge()
    kernel = AutonomyKernel(bridge=bridge, repo_root=".")
    
    # R5 task (access credentials) containing a forbidden absolute filesystem path (triggers quality veto)
    payload = {
        "target_agent": "rae-openclaw",
        "metrics": {
            "tests_passed": True,
            "coverage_before": 80.0,
            "coverage_after": 80.0
        }
    }
    
    receipt = await kernel.execute_task(
        goal_id="g-swarm-veto",
        task_id="t-swarm-veto",
        intent="Access credentials and copy secrets to database /home/usr/data.txt",
        payload=payload
    )
    
    # The swarm consensus should reject this task due to quality veto
    assert receipt.execution_status == ExecutionStatus.REJECTED
    assert receipt.final_state == TaskState.REJECTED
    assert "swarm_consensus_proposal" in payload
    assert payload["swarm_consensus_proposal"]["final_decision"] == VoteType.REJECT
    # Check that Quality veto vote was registered
    votes = payload["swarm_consensus_proposal"]["votes"]
    quality_vote = [v for v in votes if v["agent_id"] == "rae-quality"][0]
    assert quality_vote["vote"] == VoteType.REJECT
    assert "VETO" in quality_vote["reasoning"]
