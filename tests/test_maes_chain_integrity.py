import hashlib
from rae_contracts import MinimumAuditableEvent, AuditableEventType, MAESValidationStatus
from rae_auditor import ComplianceAuditor

def compute_signature(event_id, parent_event_id, sequence_no, trace_id, action, payload_hash) -> str:
    canonical_data = f"{event_id}|{parent_event_id or ''}|{sequence_no}|{trace_id}|{action}|{payload_hash}"
    return hashlib.sha256(canonical_data.encode("utf-8")).hexdigest()

def test_maes_event_signature_verification():
    auditor = ComplianceAuditor()
    
    event_id = "event-1"
    trace_id = "trace-1"
    action = "run_task"
    payload_hash = "hash1"
    sig = compute_signature(event_id, None, 0, trace_id, action, payload_hash)
    
    event = MinimumAuditableEvent(
        event_id=event_id,
        parent_event_id=None,
        sequence_no=0,
        trace_id=trace_id,
        module_id="rae-hive",
        event_type=AuditableEventType.TASK_RECEIVED,
        risk_class="R1",
        execution_mode="LIVE",
        action=action,
        payload_hash=payload_hash,
        policy_bundle_hash="policy-1",
        signing_key_id="key-1",
        signature=sig,
        human_label="Task execution root event"
    )
    
    assert auditor.verify_signature(event) is True

def test_maes_event_chain_success():
    auditor = ComplianceAuditor()
    trace_id = "trace-chain-success"
    
    # Event 0
    e0_id = "event-0"
    e0_sig = compute_signature(e0_id, None, 0, trace_id, "action0", "h0")
    e0 = MinimumAuditableEvent(
        event_id=e0_id, parent_event_id=None, sequence_no=0, trace_id=trace_id,
        module_id="rae-hive", event_type=AuditableEventType.TASK_RECEIVED,
        risk_class="R1", execution_mode="LIVE", action="action0", payload_hash="h0",
        policy_bundle_hash="p0", signing_key_id="k-1", signature=e0_sig, human_label="Start"
    )

    # Event 1
    e1_id = "event-1"
    e1_sig = compute_signature(e1_id, e0_id, 1, trace_id, "action1", "h1")
    e1 = MinimumAuditableEvent(
        event_id=e1_id, parent_event_id=e0_id, sequence_no=1, trace_id=trace_id,
        module_id="rae-hive", event_type=AuditableEventType.TOOL_INVOKED,
        risk_class="R1", execution_mode="LIVE", action="action1", payload_hash="h1",
        policy_bundle_hash="p0", signing_key_id="k-1", signature=e1_sig, human_label="Process"
    )

    findings = auditor.verify_event_chain([e0, e1])
    assert len(findings) == 0

def test_maes_event_chain_missing_root():
    auditor = ComplianceAuditor()
    trace_id = "trace-chain-missing-root"
    
    # First event has sequence_no 1 instead of 0
    e1_id = "event-1"
    e1_sig = compute_signature(e1_id, None, 1, trace_id, "action1", "h1")
    e1 = MinimumAuditableEvent(
        event_id=e1_id, parent_event_id=None, sequence_no=1, trace_id=trace_id,
        module_id="rae-hive", event_type=AuditableEventType.TASK_RECEIVED,
        risk_class="R1", execution_mode="LIVE", action="action1", payload_hash="h1",
        policy_bundle_hash="p0", signing_key_id="k-1", signature=e1_sig, human_label="Start"
    )

    findings = auditor.verify_event_chain([e1])
    assert len(findings) > 0
    assert any(f.finding_type == "MISSING_ROOT" for f in findings)
    assert e1.validation_status == MAESValidationStatus.MISSING_PARENT

def test_maes_event_chain_sequence_gap():
    auditor = ComplianceAuditor()
    trace_id = "trace-chain-gap"
    
    # Event 0
    e0_id = "event-0"
    e0_sig = compute_signature(e0_id, None, 0, trace_id, "action0", "h0")
    e0 = MinimumAuditableEvent(
        event_id=e0_id, parent_event_id=None, sequence_no=0, trace_id=trace_id,
        module_id="rae-hive", event_type=AuditableEventType.TASK_RECEIVED,
        risk_class="R1", execution_mode="LIVE", action="action0", payload_hash="h0",
        policy_bundle_hash="p0", signing_key_id="k-1", signature=e0_sig, human_label="Start"
    )

    # Event 2 (Skip sequence_no 1)
    e2_id = "event-2"
    e2_sig = compute_signature(e2_id, e0_id, 2, trace_id, "action2", "h2")
    e2 = MinimumAuditableEvent(
        event_id=e2_id, parent_event_id=e0_id, sequence_no=2, trace_id=trace_id,
        module_id="rae-hive", event_type=AuditableEventType.TOOL_INVOKED,
        risk_class="R1", execution_mode="LIVE", action="action2", payload_hash="h2",
        policy_bundle_hash="p0", signing_key_id="k-1", signature=e2_sig, human_label="Process"
    )

    findings = auditor.verify_event_chain([e0, e2])
    assert len(findings) > 0
    assert any(f.finding_type == "NON_MONOTONIC_SEQUENCE" for f in findings)
    assert e2.validation_status == MAESValidationStatus.NON_MONOTONIC_SEQUENCE

def test_maes_event_chain_broken_link():
    auditor = ComplianceAuditor()
    trace_id = "trace-chain-broken-link"
    
    # Event 0
    e0_id = "event-0"
    e0_sig = compute_signature(e0_id, None, 0, trace_id, "action0", "h0")
    e0 = MinimumAuditableEvent(
        event_id=e0_id, parent_event_id=None, sequence_no=0, trace_id=trace_id,
        module_id="rae-hive", event_type=AuditableEventType.TASK_RECEIVED,
        risk_class="R1", execution_mode="LIVE", action="action0", payload_hash="h0",
        policy_bundle_hash="p0", signing_key_id="k-1", signature=e0_sig, human_label="Start"
    )

    # Event 1 (parent_event_id mismatch)
    e1_id = "event-1"
    e1_sig = compute_signature(e1_id, "wrong-parent-id", 1, trace_id, "action1", "h1")
    e1 = MinimumAuditableEvent(
        event_id=e1_id, parent_event_id="wrong-parent-id", sequence_no=1, trace_id=trace_id,
        module_id="rae-hive", event_type=AuditableEventType.TOOL_INVOKED,
        risk_class="R1", execution_mode="LIVE", action="action1", payload_hash="h1",
        policy_bundle_hash="p0", signing_key_id="k-1", signature=e1_sig, human_label="Process"
    )

    findings = auditor.verify_event_chain([e0, e1])
    assert len(findings) > 0
    assert any(f.finding_type == "BROKEN_CHAIN" for f in findings)
    assert e1.validation_status == MAESValidationStatus.BROKEN_CHAIN
