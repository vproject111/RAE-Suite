from rae_contracts import MinimumAuditableEvent, AuditableEventType, ExecutionMode
from rae_auditor import ComplianceAuditor

def test_ledger_separation_live_write_success():
    auditor = ComplianceAuditor()
    event = MinimumAuditableEvent(
        event_id="e1", parent_event_id=None, sequence_no=0, trace_id="t1",
        module_id="rae-suite", event_type=AuditableEventType.LEDGER_COMMITTED,
        risk_class="R3", execution_mode=ExecutionMode.LIVE, action="commit", payload_hash="h1",
        policy_bundle_hash="p1", signing_key_id="k1", signature="sig1", human_label="Production write"
    )

    findings = auditor.audit_simulation_ledger_separation([event])
    assert len(findings) == 0

def test_ledger_separation_simulation_read_success():
    # Simulation reading state is perfectly fine
    auditor = ComplianceAuditor()
    event = MinimumAuditableEvent(
        event_id="e1", parent_event_id=None, sequence_no=0, trace_id="t1",
        module_id="rae-hive", event_type=AuditableEventType.SANDBOX_EXECUTED,
        risk_class="R1", execution_mode=ExecutionMode.SIMULATION_ONLY, action="sandbox", payload_hash="h1",
        policy_bundle_hash="p1", signing_key_id="k1", signature="sig1", human_label="Simulation sandbox run"
    )

    findings = auditor.audit_simulation_ledger_separation([event])
    assert len(findings) == 0

def test_ledger_separation_simulation_write_pollution():
    auditor = ComplianceAuditor()
    event = MinimumAuditableEvent(
        event_id="e1", parent_event_id=None, sequence_no=0, trace_id="t1",
        module_id="rae-suite", event_type=AuditableEventType.LEDGER_COMMITTED,
        risk_class="R3", execution_mode=ExecutionMode.SIMULATION_ONLY, action="commit", payload_hash="h1",
        policy_bundle_hash="p1", signing_key_id="k1", signature="sig1", human_label="Simulation pollution"
    )

    findings = auditor.audit_simulation_ledger_separation([event])
    assert len(findings) == 1
    assert findings[0].finding_type == "SIMULATION_POLLUTION"
    assert findings[0].severity == "CRITICAL"
