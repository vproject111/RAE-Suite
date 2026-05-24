from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

# Fallbacks for external core models to ensure Zero Warnings and test isolation
try:
    from rae_core.models.autonomy import RiskClass, ExecutionMode
except ImportError:
    class RiskClass(str, Enum):
        R0 = "R0"
        R1 = "R1"
        R2 = "R2"
        R3 = "R3"
        R4 = "R4"
        R5 = "R5"
        R6 = "R6"

    class ExecutionMode(str, Enum):
        LIVE = "LIVE"
        SIMULATION_ONLY = "SIMULATION_ONLY"
        DRY_RUN_ONLY = "DRY_RUN_ONLY"

try:
    from rae_core.models.behavior import RedactionStatus
except ImportError:
    class RedactionStatus(str, Enum):
        NOT_SCANNED = "NOT_SCANNED"
        SCANNED_SAFE = "SCANNED_SAFE"
        REDACTED = "REDACTED"

class AuditableEventType(str, Enum):
    TASK_RECEIVED = "TASK_RECEIVED"
    RISK_CLASSIFIED = "RISK_CLASSIFIED"
    POLICY_CHECKED = "POLICY_CHECKED"
    CAPABILITY_CHECKED = "CAPABILITY_CHECKED"
    TOOL_INVOKED = "TOOL_INVOKED"
    SANDBOX_EXECUTED = "SANDBOX_EXECUTED"
    QUALITY_EVALUATED = "QUALITY_EVALUATED"
    EVIDENCE_PACKED = "EVIDENCE_PACKED"
    LEDGER_COMMITTED = "LEDGER_COMMITTED"
    MEMORY_WRITTEN = "MEMORY_WRITTEN"
    QUARANTINE_TRIGGERED = "QUARANTINE_TRIGGERED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    ROLLBACK_EXECUTED = "ROLLBACK_EXECUTED"
    REPAIR_REQUESTED = "REPAIR_REQUESTED"
    PATCH_GENERATED = "PATCH_GENERATED"
    PATCH_ACCEPTED = "PATCH_ACCEPTED"
    PATCH_REJECTED = "PATCH_REJECTED"

class MAESValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"
    BROKEN_CHAIN = "BROKEN_CHAIN"
    MISSING_PARENT = "MISSING_PARENT"
    NON_MONOTONIC_SEQUENCE = "NON_MONOTONIC_SEQUENCE"
    REDACTION_REQUIRED = "REDACTION_REQUIRED"
    AUDIT_GAP = "AUDIT_GAP"

class MinimumAuditableEvent(BaseModel):
    schema_version: str = "1.0"
    event_id: str = Field(..., description="Unique event UUID")
    parent_event_id: Optional[str] = Field(None, description="Previous event UUID in this trace chain to verify chronology")
    sequence_no: int = Field(..., ge=0, description="Monotonic event sequence number within trace_id")
    trace_id: str = Field(..., description="Active session trace UUID")
    task_id: Optional[str] = Field(None, description="Active task identifier")
    module_id: str = Field(..., description="Origin module, e.g., 'rae-hive'")
    event_type: AuditableEventType = Field(..., description="Rigid event type classification")
    risk_class: RiskClass = Field(..., description="Active task risk class R0 to R6")
    execution_mode: ExecutionMode = Field(..., description="LIVE, SIMULATION_ONLY, or DRY_RUN_ONLY")
    action: str = Field(..., description="The name of the tool or action being run")
    payload_hash: str = Field(..., description="SHA-256 hash of the raw payload to prevent leaks and ensure integrity")
    redaction_status: RedactionStatus = Field(RedactionStatus.NOT_SCANNED)
    policy_bundle_hash: str = Field(..., description="Hash of active PolicyBundle used to authorize action")
    evidence_pack_hash: Optional[str] = Field(None, description="Linked EvidencePack SHA-256")
    execution_receipt_id: Optional[str] = Field(None, description="Linked final ExecutionReceipt UUID")
    signature_algorithm: str = Field("sha256", description="Signature/hash algorithm used for signing")
    signing_key_id: str = Field(..., description="Key identity used by originating module")
    signature: str = Field(..., description="Cryptographic signature signed by the originating module key")
    validation_status: MAESValidationStatus = Field(MAESValidationStatus.VALID, description="Compliance and event-chain validation status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    human_label: str = Field(..., description="ISO 27001-compliant human scannable action description")
