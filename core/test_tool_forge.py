import pytest
from unittest.mock import MagicMock
from core.capability_registry import CapabilityRegistry
from core.sandbox_manager import SandboxManager
from core.quality_sentinel import QualitySentinel
from core.test_integrity_guard import TestIntegrityGuard
from core.tool_forge import ToolForge
from rae_core.models.capabilities import AgentRegistration

class MockBridge:
    def log_decision(self, action, reasoning, payload):
        pass
    def save_event(self, text, layer="episodic"):
        pass

@pytest.mark.asyncio
async def test_tool_forge_successful_registration():
    registry = CapabilityRegistry()
    sandbox_manager = SandboxManager(".")
    quality_sentinel = QualitySentinel(TestIntegrityGuard())
    
    forge = ToolForge(registry, sandbox_manager, quality_sentinel)
    
    # Forge a valid tool
    res = await forge.forge_tool(
        tool_name="url_cleaner",
        description="Helper to sanitize URL endpoints relatively",
        agent_id="agent-developer"
    )
    
    assert res is True
    
    # Check registration details in CapabilityRegistry
    agent_reg = registry._agents.get("agent-developer")
    assert agent_reg is not None
    assert len(agent_reg.capabilities) == 1
    assert agent_reg.capabilities[0].name == "url_cleaner"
    assert agent_reg.capabilities[0].description == "Helper to sanitize URL endpoints relatively"

@pytest.mark.asyncio
async def test_tool_forge_rejection_due_to_constitutional_violation():
    registry = CapabilityRegistry()
    sandbox_manager = SandboxManager(".")
    quality_sentinel = QualitySentinel(TestIntegrityGuard())
    
    forge = ToolForge(registry, sandbox_manager, quality_sentinel)
    
    # Forge a tool that has bad keywords to trigger violation
    # E.g. we override _generate_tool_code to return a script that violates C6 (absolute path)
    forge._generate_tool_code = lambda n, d: "import os\npath = '/home/grzegorz-lesniowski/restricted.txt'"
    
    res = await forge.forge_tool(
        tool_name="bad_parser",
        description="Parsing violating paths",
        agent_id="agent-developer"
    )
    
    # Should be rejected because the code contains absolute path '/home/'
    assert res is False
    
    agent_reg = registry._agents.get("agent-developer")
    if agent_reg:
        # Should not have bad_parser registered
        assert len([c for c in agent_reg.capabilities if c.name == "bad_parser"]) == 0
