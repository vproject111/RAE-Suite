import pytest
import sys
import os

# Ensure src is in sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from fabric.capability_lattice import CapabilityLattice
from fabric.cost_aware_router import CostAwareRouter
from fabric.contract_validator import ContractValidator
from fabric.fabric_telemetry import FabricTelemetry

from pydantic import BaseModel, Field

class DummyPayload(BaseModel):
    name: str
    tokens: int = Field(..., gt=0)

def test_capability_lattice():
    lattice = CapabilityLattice()
    lattice.link_capabilities("generate_code", "lint_code")
    lattice.link_capabilities("generate_code", "run_tests")
    
    deps = lattice.get_dependencies("generate_code")
    assert len(deps) == 2
    assert "lint_code" in deps
    assert "run_tests" in deps


def test_cost_aware_router():
    router = CostAwareRouter()
    
    # Mock agents/executors
    agents = [
        {
            "agent_id": "agent-cheap-local",
            "capabilities": ["generate_code"],
            "risk_class": "low",
            "estimated_ncu": 0.05,
            "failure_rate_30d": 0.02,
            "latency_p50_s": 0.8
        },
        {
            "agent_id": "agent-expensive-api",
            "capabilities": ["generate_code"],
            "risk_class": "high",
            "estimated_ncu": 2.5,
            "failure_rate_30d": 0.005,
            "latency_p50_s": 1.5
        }
    ]
    
    # Route for low risk -> should select the cheap local agent
    best = router.route("generate_code", agents, max_risk="low")
    assert best is not None
    assert best["agent_id"] == "agent-cheap-local"
    
    # Route for high risk with max_risk limit = high -> cheap local is still cheaper and has low risk, so it gets sorted first
    best_high = router.route("generate_code", agents, max_risk="high")
    assert best_high["agent_id"] == "agent-cheap-local"
    
    # If cheap agent is filtered out (e.g. only high risk allowed and max_risk=medium), return None
    best_filtered = router.route("generate_code", [agents[1]], max_risk="medium")
    assert best_filtered is None


def test_contract_validator():
    validator = ContractValidator()
    
    # Valid payload
    assert validator.validate_payload(DummyPayload, {"name": "test", "tokens": 100})
    
    # Invalid payload (tokens <= 0)
    assert not validator.validate_payload(DummyPayload, {"name": "test", "tokens": -5})


def test_fabric_telemetry():
    telemetry = FabricTelemetry()
    telemetry.record_call("generate_code", 120.0, "success")
    telemetry.record_call("generate_code", 80.0, "success")
    telemetry.record_call("generate_code", 100.0, "failure")
    
    m = telemetry.metrics["generate_code"]
    assert m["calls"] == 3
    assert m["failures"] == 1
    assert m["avg_latency"] == 100.0
