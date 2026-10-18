import pytest
from fastapi.testclient import TestClient

from rae_contracts import (
    TaskState,
    TransitionContract,
    TransitionAuthorizationError,
    TransitionGuardError,
)
from core.autonomy_kernel import AutonomyKernel, FatalEnterpriseError
from src.fabric.cost_aware_router import CostAwareRouter
from main import app


def test_adr001_transition_contract_authorize_and_guard():
    contract = TransitionContract(
        from_state=TaskState.RECEIVED,
        to_state=TaskState.CLASSIFIED,
        cycle_limit=2,
    )
    st = contract.apply(actor="autonomy-kernel", reason="classified ok", cycle_count=1)
    assert st.from_state == TaskState.RECEIVED
    assert st.to_state == TaskState.CLASSIFIED

    with pytest.raises(TransitionAuthorizationError):
        contract.apply(actor="untrusted-actor", cycle_count=1)

    with pytest.raises(TransitionGuardError):
        contract.apply(actor="autonomy-kernel", cycle_count=3)


@pytest.mark.asyncio
async def test_autonomy_kernel_idempotency_key_and_speculative_execution():
    kernel = AutonomyKernel(repo_root=".")
    r1 = await kernel.execute_task(
        goal_id="g-idem-1",
        task_id="t-idem-1",
        intent="Read status",
        payload={"speculative_commands": [["git", "status"]]},
        idempotency_key="idem-key-001",
    )
    r2 = await kernel.execute_task(
        goal_id="g-idem-1",
        task_id="t-idem-1",
        intent="Read status",
        payload={"speculative_commands": [["git", "status"]]},
        idempotency_key="idem-key-001",
    )
    assert r1.id == r2.id
    assert len(kernel.transition_attempts) > 0

    with pytest.raises(FatalEnterpriseError):
        await kernel.execute_task(
            goal_id="g-idem-1",
            task_id="t-idem-1",
            intent="Different intent with same idempotency key",
            idempotency_key="idem-key-001",
        )


def test_cost_aware_router_mab_weights():
    router = CostAwareRouter()
    agents = [
        {
            "agent_id": "agent-fast-expensive",
            "capabilities": ["code.review"],
            "risk_class": "low",
            "failure_rate_30d": 0.01,
            "latency_p50_s": 0.2,
            "estimated_ncu": 10.0,
        },
        {
            "agent_id": "agent-slow-cheap",
            "capabilities": ["code.review"],
            "risk_class": "low",
            "failure_rate_30d": 0.05,
            "latency_p50_s": 5.0,
            "estimated_ncu": 0.5,
        },
    ]
    # Default routing prefers lowest estimated_ncu
    default_choice = router.route("code.review", agents)
    assert default_choice["agent_id"] == "agent-slow-cheap"

    # High beta (latency sensitivity) prefers fast agent
    mab_choice = router.route(
        "code.review",
        agents,
        weights={"alpha": 0.1, "beta": 0.85, "gamma": 0.05},
    )
    assert mab_choice["agent_id"] == "agent-fast-expensive"


def test_control_plane_new_v2_endpoints():
    client = TestClient(app)

    # 1. /health
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["version"] == "3.9.0"

    # 2. /v2/kernel/execute
    r_exec = client.post(
        "/v2/kernel/execute",
        json={"goal_id": "g-api", "task_id": "t-api", "intent": "Check status"},
    )
    assert r_exec.status_code == 200
    assert r_exec.json()["execution_status"] == "SUCCESS"

    # 3. /v2/portal/overview
    r_ov = client.get("/v2/portal/overview")
    assert r_ov.status_code == 200
    assert r_ov.json()["status"] == "ALL_SYSTEMS_OPERATIONAL"

    # 4. /v2/portal/hitl/request & approve & iso-report
    r_req = client.post(
        "/v2/portal/hitl/request",
        json={
            "target_module": "rae-suite",
            "action_name": "deploy_prod",
            "risk_class": "R4",
            "requested_by": "test-agent",
        },
    )
    assert r_req.status_code == 200
    req_id = r_req.json()["request_id"]

    r_app = client.post(
        "/v2/portal/hitl/approve",
        json={"request_id": req_id, "approved": True, "approver": "grzegorz"},
    )
    assert r_app.status_code == 200
    assert r_app.json()["status"] == "APPROVED"

    r_iso = client.get("/v2/portal/hitl/iso-report")
    assert r_iso.status_code == 200
    assert r_iso.json()["iso_27001_status"] == "COMPLIANT"

    # 5. /v2/knowledge/resolve
    r_know = client.post(
        "/v2/knowledge/resolve",
        json={"query": "HEAD", "tenant_id": "default", "request_id": "req-api-1"},
    )
    assert r_know.status_code == 200
    assert "content_hash" in r_know.json()
    assert "audit_hash" in r_know.json()
