import os
import sys
from pathlib import Path

# Fix PYTHONPATH for internal packages
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "packages" / "rae-core" / "src"))
sys.path.append(str(BASE_DIR / "rae_core" / "src"))
sys.path.append(str(BASE_DIR / "packages" / "rae-quality"))

from fastapi import FastAPI, HTTPException
from typing import Any, List, Dict, Optional
from rae_core.models.capabilities import AgentRegistration
from rae_core.models.behavior import DepartmentBehaviorContract, BehaviorSignal
from core.auditor_engine import AuditorEngine
from core.behavior_registry import BehaviorRegistry
from core.capability_registry import CapabilityRegistry
from core.reconcile import Reconciler
from core.factory import FactorySpec
from fabric.cost_aware_router import CostAwareRouter
from engines.governance.quality_gateway_v2 import RAEQualityGatewayV2

app = FastAPI(title="RAE-Suite Control Plane v2.0 (Master)")

# Inicjalizacja komponentów
cap_registry = CapabilityRegistry()
beh_registry = BehaviorRegistry()
auditor = AuditorEngine()
router = CostAwareRouter()
default_spec = FactorySpec(factory_id="master-factory", active_departments=[], agents={}, budgets={})
reconciler = Reconciler(default_spec)
quality_gateway_v2 = RAEQualityGatewayV2()

@app.get("/health")
async def health():
    return {
        "status": "operational",
        "version": "3.8.4",
        "api": "v2",
        "quality_v2": "integrated",
    }

@app.get("/v2/factory/reconcile")
async def factory_reconcile():
    return await reconciler.reconcile_all()

@app.post("/v2/departments/register")
async def register_department(reg: AgentRegistration):
    cap_registry.register(reg)
    return {"status": "registered", "agent_id": reg.agent_id}

@app.get("/v2/fabric/route")
async def route_task(capability_id: str, max_risk: str = "high"):
    agents = [vars(a) for a in cap_registry._agents.values()]
    decision = router.route(capability_id, agents, max_risk)
    if not decision:
        raise HTTPException(status_code=404, detail=f"No agent for {capability_id}")
    return decision

@app.post("/v2/audit/evaluate")
async def audit_evaluate(department: str, raw_signals: List[dict]):
    contract = beh_registry.get(department)
    if not contract:
        raise HTTPException(status_code=404, detail=f"No contract for {department}")
    signals = auditor.collect_behavior_signals(raw_signals)
    violations = auditor.evaluate_behavioral_contract(contract, signals)
    return {"verdict": "BLOCKED" if violations else "PASSED", "violations": violations}

# --- Integrated RAE-Quality 2.0 Endpoints inside RAE-Suite ---
@app.post("/v2/quality/rpc")
async def suite_quality_rpc(payload: Dict[str, Any]):
    op = payload.get("operation", "quality.report")
    params = payload.get("params", {})
    try:
        return quality_gateway_v2.dispatch_rpc(op, params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/v2/quality/policy")
async def suite_quality_policy(payload: Dict[str, Any]):
    return quality_gateway_v2.get_policy(payload)

@app.post("/v2/quality/analyze-diff")
async def suite_quality_analyze_diff(payload: Dict[str, Any]):
    return quality_gateway_v2.analyze_diff(payload)

@app.post("/v2/quality/security-scan")
async def suite_quality_security_scan(payload: Dict[str, Any]):
    return quality_gateway_v2.security_scan(payload)

@app.post("/v2/quality/generate-tests")
async def suite_quality_generate_tests(payload: Dict[str, Any]):
    return quality_gateway_v2.generate_tests(payload)

@app.post("/v2/quality/verify-fix")
async def suite_quality_verify_fix(payload: Dict[str, Any]):
    return quality_gateway_v2.verify_fix(payload)

@app.post("/v2/quality/check-architecture")
async def suite_quality_check_architecture(payload: Dict[str, Any]):
    return quality_gateway_v2.check_architecture(payload)

@app.post("/v2/quality/release-gate")
async def suite_quality_release_gate(payload: Dict[str, Any]):
    return quality_gateway_v2.release_gate(payload)

@app.get("/v2/quality/report")
async def suite_quality_report():
    return quality_gateway_v2.report()

