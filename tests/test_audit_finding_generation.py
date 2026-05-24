import hashlib
from rae_contracts import (
    MinimumAuditableEvent,
    AuditableEventType,
    ComplianceStatus,
    AuditFindingSeverity
)
from core.auditor_engine import AuditorEngine

def compute_signature(event_id, parent_event_id, sequence_no, trace_id, action, payload_hash) -> str:
    canonical_data = f"{event_id}|{parent_event_id or ''}|{sequence_no}|{trace_id}|{action}|{payload_hash}"
    return hashlib.sha256(canonical_data.encode("utf-8")).hexdigest()

def test_auditor_engine_audit_success():
    engine = AuditorEngine()
    trace_id = "trace-test-success"
    
    # Generate clean events
    e0_id = "e0"
    e0_sig = compute_signature(e0_id, None, 0, trace_id, "action0", "h0")
    e0 = MinimumAuditableEvent(
        event_id=e0_id, parent_event_id=None, sequence_no=0, trace_id=trace_id,
        module_id="rae-core", event_type=AuditableEventType.TASK_RECEIVED,
        risk_class="R0", execution_mode="LIVE", action="action0", payload_hash="h0",
        policy_bundle_hash="p0", signing_key_id="k1", signature=e0_sig, human_label="Start"
    )

    report = engine.audit_maes_events([e0], ["Raw start log"])
    
    assert report.compliance_status == ComplianceStatus.COMPLIANT
    assert len(report.findings) == 0
    assert report.evidence_source == trace_id

def test_auditor_engine_audit_critical_pollution():
    engine = AuditorEngine()
    trace_id = "trace-test-pollution"
    
    # Generate simulated write event (critical pollution)
    e0_id = "e0"
    e0_sig = compute_signature(e0_id, None, 0, trace_id, "commit", "h0")
    e0 = MinimumAuditableEvent(
        event_id=e0_id, parent_event_id=None, sequence_no=0, trace_id=trace_id,
        module_id="rae-suite", event_type=AuditableEventType.LEDGER_COMMITTED,
        risk_class="R3", execution_mode="SIMULATION_ONLY", action="commit", payload_hash="h0",
        policy_bundle_hash="p0", signing_key_id="k1", signature=e0_sig, human_label="Pollution"
    )

    report = engine.audit_maes_events([e0])
    
    assert report.compliance_status == ComplianceStatus.NON_COMPLIANT
    assert len(report.findings) == 1
    assert report.findings[0].finding_type == "SIMULATION_POLLUTION"
    assert report.findings[0].severity == AuditFindingSeverity.CRITICAL

def test_auditor_engine_audit_secret_leak():
    engine = AuditorEngine()
    trace_id = "trace-test-secret-leak"
    
    e0_id = "e0"
    e0_sig = compute_signature(e0_id, None, 0, trace_id, "sandbox", "h0")
    e0 = MinimumAuditableEvent(
        event_id=e0_id, parent_event_id=None, sequence_no=0, trace_id=trace_id,
        module_id="rae-hive", event_type=AuditableEventType.SANDBOX_EXECUTED,
        risk_class="R1", execution_mode="LIVE", action="sandbox", payload_hash="h0",
        policy_bundle_hash="p0", signing_key_id="k1", signature=e0_sig, human_label="Sandbox run"
    )

    leak_payload = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA08gD4...\n"
    report = engine.audit_maes_events([e0], [leak_payload])
    
    assert report.compliance_status == ComplianceStatus.NON_COMPLIANT
    assert len(report.findings) == 1
    assert report.findings[0].finding_type == "SECRET_LEAK"
    assert report.findings[0].severity == AuditFindingSeverity.HIGH
