import pytest
from core.tool_gateway import ToolGateway
from core.speculative_executor import SpeculativeToolExecutor
from rae_contracts import RiskClass

@pytest.mark.anyio
async def test_speculative_executor_safe_commands():
    gateway = ToolGateway(".")
    executor = SpeculativeToolExecutor(gateway)
    
    # Mix of safe and unsafe commands
    commands = [
        ["git", "status"],                   # Safe (read-only)
        ["docker", "ps"],                    # Safe (read-only)
        ["rm", "-rf", "/"],                  # Unsafe (not allowed)
        ["git", "commit", "-m", "bad"]       # Unsafe (mutates git repo state)
    ]
    
    results = await executor.execute_speculatively(
        trace_id="test-speculative-trace",
        commands=commands,
        risk_class=RiskClass.R0
    )
    
    # Check that only safe commands were run (max k=3)
    assert len(results) == 2
    assert "git status" in results
    assert "docker ps" in results
    assert "rm -rf /" not in results
    assert "git commit -m bad" not in results
