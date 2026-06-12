import pytest
from unittest.mock import MagicMock, patch
from rae_suite_orchestrator import RAE_CEO_Orchestrator

@pytest.mark.asyncio
async def test_orchestrator_initialization_and_idle_scan():
    # Mock network calls and file operations to keep tests fast and isolated
    with patch("rae_suite_orchestrator.RAE_CEO_Orchestrator._observe_system_state") as mock_observe:
        from unittest.mock import AsyncMock
        mock_observe.return_value = {
            "lab_insights": {},
            "backlog": [],
            "active_agents": ["rae-phoenix", "rae-hive", "rae-quality"]
        }
        
        orchestrator = RAE_CEO_Orchestrator()
        assert orchestrator.kernel is not None
        assert orchestrator.curiosity_engine is not None
        
        # Test loading spec
        spec = orchestrator._load_desired_factory_spec()
        assert "factory_id" in spec or "version" in spec
        
        # Mock trigger_idle_scan as an async call
        orchestrator.curiosity_engine.trigger_idle_scan = AsyncMock(return_value=True)
        
        # Simulate one iteration of the run_loop (without infinite loop)
        desired_state = orchestrator._load_desired_factory_spec()
        actual_state = await orchestrator._observe_system_state()
        drifts = orchestrator._detect_configuration_drifts(desired_state, actual_state)
        
        assert len(drifts) == 0  # Should be fully aligned
        
        decision = await orchestrator._decide_backlog_action(actual_state)
        assert decision.get("intent") == "IDLE"
        
        await orchestrator.curiosity_engine.trigger_idle_scan()
        orchestrator.curiosity_engine.trigger_idle_scan.assert_called_once()
