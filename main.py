import os
import sys
from pathlib import Path

# Fix PYTHONPATH for internal packages
BASE_DIR = Path(__file__).resolve().parent
for _p in [
    BASE_DIR / "packages" / "rae-core" / "src",
    BASE_DIR / "rae_core" / "src",
    BASE_DIR / "packages" / "rae-agentic-memory" / "rae-core",
    BASE_DIR / "packages" / "rae-agentic-memory",
    BASE_DIR / "packages" / "rae-quality",
]:
    if str(_p) not in sys.path:
        sys.path.append(str(_p))

from fastapi import FastAPI, HTTPException
from typing import Any, List, Dict, Optional
from rae_core.models.capabilities import AgentRegistration
from rae_core.models.behavior import DepartmentBehaviorContract, BehaviorSignal
from core.auditor_engine import AuditorEngine
from core.behavior_registry import BehaviorRegistry
from core.capability_registry import CapabilityRegistry
from core.reconcile import Reconciler
from core.factory import FactorySpec
from core.autonomy_kernel import AutonomyKernel
from core.layer_triad_runner import LayerTriadRunner
from core.portal_dashboards import PortalDashboardAggregator
from core.portal_hitl_approval import PortalHITLApprovalEngine
from rae_contracts import RiskClass
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
autonomy_kernel = AutonomyKernel(repo_root=str(BASE_DIR))
triad_runner = LayerTriadRunner()
portal_dashboard = PortalDashboardAggregator()
portal_hitl = PortalHITLApprovalEngine()

@app.get("/health")
async def health():
    return {
        "status": "operational",
        "version": "3.9.0",
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

# --- Integrated AutonomyKernel, LayerTriadRunner, Portal & Knowledge Endpoints ---
@app.post("/v2/kernel/execute")
async def suite_kernel_execute(payload: Dict[str, Any]):
    goal_id = payload.get("goal_id", "api-goal")
    task_id = payload.get("task_id", "api-task")
    intent = payload.get("intent", "Execute task")
    task_payload = payload.get("payload", {}) or {}
    human_approved = bool(payload.get("human_approved", False))
    idempotency_key = payload.get("idempotency_key")
    kwargs: Dict[str, Any] = {
        "goal_id": goal_id,
        "task_id": task_id,
        "intent": intent,
        "payload": task_payload,
        "human_approved": human_approved,
    }
    if idempotency_key is not None:
        kwargs["idempotency_key"] = idempotency_key
    receipt = await autonomy_kernel.execute_task(**kwargs)
    return receipt.model_dump() if hasattr(receipt, "model_dump") else receipt.__dict__

@app.post("/v2/triad/run")
async def suite_triad_run(payload: Dict[str, Any]):
    tier = payload.get("tier", "tier1_generate")
    text = payload.get("text") or payload.get("prompt") or ""
    if tier == "cascade" or payload.get("cascade"):
        return await triad_runner.execute_3tier_cascade(task_text=text)
    return await triad_runner.execute_layer_triad(layer_name=tier, payload_text=text)

@app.get("/v2/portal/overview")
async def suite_portal_overview():
    return portal_dashboard.get_full_command_center_overview()

@app.post("/v2/portal/hitl/request")
async def suite_portal_hitl_request(payload: Dict[str, Any]):
    target_module = payload.get("target_module", "rae-suite")
    action_name = payload.get("action_name", "restricted_action")
    risk_str = payload.get("risk_class", "R4_EXTERNAL_WRITE")
    requested_by = payload.get("requested_by", "agent")
    try:
        risk_class = RiskClass(risk_str)
    except ValueError:
        risk_class = RiskClass.R4_EXTERNAL_WRITE
    req = portal_hitl.create_approval_request(
        target_module=target_module,
        action_name=action_name,
        risk_class=risk_class,
        requested_by=requested_by,
    )
    return req.model_dump()

@app.post("/v2/portal/hitl/approve")
async def suite_portal_hitl_approve(payload: Dict[str, Any]):
    request_id = payload.get("request_id", "")
    approved = bool(payload.get("approved", True))
    approver = payload.get("approver", "operator")
    reason = payload.get("reason", "")
    try:
        req = portal_hitl.process_approval(
            request_id=request_id,
            approved=approved,
            approver=approver,
            reason=reason,
        )
        return req.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/v2/portal/hitl/iso-report")
async def suite_portal_hitl_iso_report():
    return portal_hitl.get_iso_compliance_report().model_dump()

@app.post("/v2/knowledge/resolve")
async def suite_knowledge_resolve(payload: Dict[str, Any]):
    query = payload.get("query", "")
    if not query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")
    tenant_id = payload.get("tenant_id", "default")
    request_id = payload.get("request_id", "api-req-1")
    scope = payload.get("scope") or []

    from rae_core.governance.adapter_broker import AdapterBroker
    from rae_core.governance.context import ResolutionContext
    from rae_core.governance.engine import DefaultKnowledgeResolutionEngine
    adapters = []
    try:
        from rae_adapters.git_adapter import GitRuntimeAdapter
        adapters.append(GitRuntimeAdapter(str(BASE_DIR)))
    except Exception:
        pass
    broker = AdapterBroker(adapters)
    engine = DefaultKnowledgeResolutionEngine(broker)
    ctx = ResolutionContext(
        tenant_id=tenant_id,
        request_id=request_id,
        policy_version="1.0.0",
        scope=tuple(scope) if scope else (),
    )
    bundle = await engine.resolve(query, context=ctx)
    return bundle.model_dump() if hasattr(bundle, "model_dump") else bundle.__dict__

