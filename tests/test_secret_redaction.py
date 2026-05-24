from rae_contracts import MinimumAuditableEvent, AuditableEventType, MAESValidationStatus, RedactionStatus
from rae_auditor import ComplianceAuditor

def test_secret_redaction_clean_payload():
    auditor = ComplianceAuditor()
    event = MinimumAuditableEvent(
        event_id="e1", parent_event_id=None, sequence_no=0, trace_id="t1",
        module_id="rae-hive", event_type=AuditableEventType.SANDBOX_EXECUTED,
        risk_class="R1", execution_mode="LIVE", action="sandbox", payload_hash="h1",
        policy_bundle_hash="p1", signing_key_id="k1", signature="sig1",
        redaction_status=RedactionStatus.NOT_SCANNED, human_label="Exec clean"
    )

    clean_payload = "Building source code, compiling binaries. Exit code: 0."
    findings = auditor.check_secret_redaction(event, clean_payload)
    assert len(findings) == 0
    assert event.validation_status == MAESValidationStatus.VALID

def test_secret_redaction_private_key_leak():
    auditor = ComplianceAuditor()
    event = MinimumAuditableEvent(
        event_id="e1", parent_event_id=None, sequence_no=0, trace_id="t1",
        module_id="rae-hive", event_type=AuditableEventType.SANDBOX_EXECUTED,
        risk_class="R1", execution_mode="LIVE", action="sandbox", payload_hash="h1",
        policy_bundle_hash="p1", signing_key_id="k1", signature="sig1",
        redaction_status=RedactionStatus.NOT_SCANNED, human_label="Exec leak"
    )

    leak_payload = """
    Connecting to remote server...
    -----BEGIN RSA PRIVATE KEY-----
    MIIEowIBAAKCAQEA08gD4...
    -----END RSA PRIVATE KEY-----
    Connection established.
    """
    findings = auditor.check_secret_redaction(event, leak_payload)
    assert len(findings) == 1
    assert findings[0].finding_type == "SECRET_LEAK"
    assert event.validation_status == MAESValidationStatus.REDACTION_REQUIRED

def test_secret_redaction_token_assignment_leak():
    auditor = ComplianceAuditor()
    event = MinimumAuditableEvent(
        event_id="e1", parent_event_id=None, sequence_no=0, trace_id="t1",
        module_id="rae-hive", event_type=AuditableEventType.SANDBOX_EXECUTED,
        risk_class="R1", execution_mode="LIVE", action="sandbox", payload_hash="h1",
        policy_bundle_hash="p1", signing_key_id="k1", signature="sig1",
        redaction_status=RedactionStatus.NOT_SCANNED, human_label="Exec leak"
    )

    leak_payload = 'Configuring environmental variables: TOKEN="super_secret_api_token_val_123"'
    findings = auditor.check_secret_redaction(event, leak_payload)
    assert len(findings) == 1
    assert findings[0].finding_type == "SECRET_LEAK"
    assert event.validation_status == MAESValidationStatus.REDACTION_REQUIRED

def test_secret_redaction_already_redacted_safe():
    auditor = ComplianceAuditor()
    event = MinimumAuditableEvent(
        event_id="e1", parent_event_id=None, sequence_no=0, trace_id="t1",
        module_id="rae-hive", event_type=AuditableEventType.SANDBOX_EXECUTED,
        risk_class="R1", execution_mode="LIVE", action="sandbox", payload_hash="h1",
        policy_bundle_hash="p1", signing_key_id="k1", signature="sig1",
        redaction_status=RedactionStatus.REDACTED, human_label="Exec redacted"
    )

    # Payload contains sensitive patterns, but redaction_status is marked REDACTED
    leak_payload = 'Configuring environmental variables: TOKEN="[REDACTED]"'
    findings = auditor.check_secret_redaction(event, leak_payload)
    
    # Skaner nie zgłosi naruszenia, ponieważ event został oznaczony jako zredagowany
    assert len(findings) == 0
    assert event.validation_status == MAESValidationStatus.VALID
