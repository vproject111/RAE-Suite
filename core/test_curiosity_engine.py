import os
import pytest
from unittest.mock import MagicMock
from core.curiosity_engine import CuriosityEngine
from core.autonomy_kernel import AutonomyKernel
from rae_contracts import TaskState, ExecutionStatus, QualityStatus

class MockBridge:
    def log_decision(self, action, reasoning, payload):
        pass
    def save_event(self, text, layer="episodic"):
        pass

def test_curiosity_engine_analysis_logic(tmp_path):
    # Create a mock file with missing type hints and unused imports
    mock_file = tmp_path / "mock_service.py"
    mock_file.write_text("""import sys  # Unused import
import json

def process_data(data):  # Missing type hints
    return json.dumps(data)
""")
    
    kernel = MagicMock()
    engine = CuriosityEngine(kernel, str(tmp_path))
    
    issues = engine._analyze_file(str(mock_file), "mock_service.py")
    
    # Verify both issues are detected
    issue_types = [issue["type"] for issue in issues]
    assert "Unused Imports" in issue_types
    assert "Missing Type Hints" in issue_types
    
    # Check details
    unused_import_issue = next(i for i in issues if i["type"] == "Unused Imports")
    assert "sys" in unused_import_issue["details"]

@pytest.mark.asyncio
async def test_curiosity_engine_trigger_idle_scan():
    bridge = MockBridge()
    kernel = AutonomyKernel(bridge=bridge, repo_root=".")
    
    engine = CuriosityEngine(kernel, ".")
    
    # Mock _scan_codebase to return a single mock issue to control execution
    engine._scan_codebase = lambda: [{
        "type": "Missing Type Hints",
        "file": "core/policy_checker.py",
        "details": "Function check_compliance is missing type annotations."
    }]
    
    # Trigger idle scan
    success = await engine.trigger_idle_scan()
    
    # Verify it executed and completed successfully
    assert success is True
