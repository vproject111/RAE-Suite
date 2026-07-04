import pytest
import os
import subprocess
from unittest.mock import MagicMock, patch
from core.autonomy_kernel import AutonomyKernel
from rae_contracts import ExecutionStatus, TaskState

class MockBridge:
    def log_decision(self, action, reasoning, payload):
        pass
    def save_event(self, text, layer="episodic"):
        pass

@pytest.mark.asyncio
async def test_ssh_offloading_success():
    bridge = MockBridge()
    kernel = AutonomyKernel(bridge=bridge, repo_root=".")
    
    # Payload requesting rae-openclaw (forces execution block)
    payload = {
        "target_agent": "rae-openclaw",
        "original_test": "def test_f(): assert True",
        "modified_test": "def test_f(): assert True",
        "metrics": {
            "tests_passed": True,
            "coverage_before": 80.0,
            "coverage_after": 80.1
        }
    }
    
    with patch("os.getenv") as mock_getenv, \
         patch("os.path.exists", return_value=True), \
         patch("subprocess.run") as mock_run:
        
        # Setup env mock
        def getenv_side_effect(key, default=None):
            if key == "EXECUTION_HOST":
                return "100.68.166.117"
            if key == "EXECUTION_SSH_USER":
                return "operator"
            if key == "EXECUTION_REMOTE_WORKSPACE":
                return "~/rae-node-agent"
            return default
        mock_getenv.side_effect = getenv_side_effect
        
        # Setup subprocess run mock to succeed on first try (SSH)
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Remote success"
        mock_run.return_value = mock_proc
        
        receipt = await kernel.execute_task(
            goal_id="g-ssh",
            task_id="t-ssh",
            intent="Run openclaw task",
            payload=payload
        )
        
        assert receipt.execution_status == ExecutionStatus.SUCCESS
        
        # Assert subprocess was called with ssh command
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert "ssh" in args[0]
        assert "operator@100.68.166.117" in args[0]

@pytest.mark.asyncio
async def test_ssh_offloading_fallback_to_local_on_failure():
    bridge = MockBridge()
    kernel = AutonomyKernel(bridge=bridge, repo_root=".")
    
    payload = {
        "target_agent": "rae-openclaw",
        "original_test": "def test_f(): assert True",
        "modified_test": "def test_f(): assert True",
        "metrics": {
            "tests_passed": True,
            "coverage_before": 80.0,
            "coverage_after": 80.1
        }
    }
    
    with patch("os.getenv") as mock_getenv, \
         patch("os.path.exists", return_value=True), \
         patch("subprocess.run") as mock_run:
        
        def getenv_side_effect(key, default=None):
            if key == "EXECUTION_HOST":
                return "100.68.166.117"
            if key == "EXECUTION_SSH_USER":
                return "operator"
            if key == "EXECUTION_REMOTE_WORKSPACE":
                return "~/rae-node-agent"
            return default
        mock_getenv.side_effect = getenv_side_effect
        
        # Setup subprocess run mock:
        # First call (SSH) fails with returncode = 255 (or similar connection failure)
        # Second call (local) succeeds with returncode = 0
        mock_proc_fail = MagicMock()
        mock_proc_fail.returncode = 255
        mock_proc_fail.stderr = "SSH connection timeout"
        
        mock_proc_success = MagicMock()
        mock_proc_success.returncode = 0
        mock_proc_success.stdout = "Local fallback success"
        
        mock_run.side_effect = [mock_proc_fail, mock_proc_success]
        
        receipt = await kernel.execute_task(
            goal_id="g-ssh-fallback",
            task_id="t-ssh-fallback",
            intent="Run openclaw task with fallback",
            payload=payload
        )
        
        assert receipt.execution_status == ExecutionStatus.SUCCESS
        assert mock_run.call_count == 2
        
        # Verify first call was SSH, second was local
        first_call_args = mock_run.call_args_list[0][0][0]
        second_call_args = mock_run.call_args_list[1][0][0]
        
        assert "ssh" in first_call_args
        assert "ssh" not in second_call_args
        assert "node" in second_call_args
