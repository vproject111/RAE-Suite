from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

# Dynamic imports with fallbacks to guarantee isolated test compilation
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

class ToolInvocationEvent(BaseModel):
    schema_version: str = "1.0"
    tool_invocation_id: str = Field(..., description="Unique tool invocation UUID")
    trace_id: str = Field(..., description="Active trace UUID to bind context")
    task_id: Optional[str] = Field(None, description="Active task identifier")
    module_id: str = Field("rae-hive", description="Originating module")
    risk_class: RiskClass = Field(..., description="Risk class rating of the command execution")
    execution_mode: ExecutionMode = Field(..., description="Active execution state")
    tool_name: str = Field(..., description="The low-level binary or command name")
    arguments_hash: str = Field(..., description="SHA-256 hash of execution arguments")
    working_directory_hash: str = Field(..., description="SHA-256 of active sandbox path")
    container_image_digest: str = Field(..., description="Docker registry digest verification")
    stdout_hash: str = Field(..., description="SHA-256 hash of execution stdout stream")
    stderr_hash: str = Field(..., description="SHA-256 hash of execution stderr stream")
    redacted_stdout_uri: Optional[str] = Field(None, description="Optional URI reference to redacted stdout storage")
    redacted_stderr_uri: Optional[str] = Field(None, description="Optional URI reference to redacted stderr storage")
    exit_code: int = Field(..., description="Process exit status")
    duration_ms: float = Field(..., ge=0, description="Measured execution time in milliseconds")
    redaction_status: RedactionStatus = Field(RedactionStatus.REDACTED, description="Strict enforcement flag")
    evidence_pack_hash: Optional[str] = Field(None, description="Linked EvidencePack SHA-256 containing raw artifacts")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PhoenixRepairDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DEGRADED = "DEGRADED"
    ESCALATED = "ESCALATED"

class PhoenixRepairIteration(BaseModel):
    schema_version: str = "1.0"
    repair_iteration_id: str = Field(..., description="Unique identifier of the repair run")
    trace_id: str = Field(..., description="Active session trace UUID")
    attempt_no: int = Field(..., ge=1, description="Monotonic retry/iteration counter")
    input_error_hash: str = Field(..., description="SHA-256 hash of the target build error stack trace")
    patch_diff_hash: str = Field(..., description="SHA-256 hash of the proposed unified patch diff")
    quality_gate_result_id: str = Field(..., description="Associated static/mutation audit score ID")
    evidence_pack_hash: str = Field(..., description="Compressed diagnostic artifacts package SHA-256")
    rollback_plan_id: Optional[str] = Field(None, description="Associated automated rollback recipe ID")
    stop_condition_triggered: bool = Field(False, description="Whether termination limits were hit")
    final_decision: PhoenixRepairDecision = Field(..., description="Final repair status result")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GuardrailLifecycleState(str, Enum):
    CANDIDATE = "CANDIDATE"
    SHADOW = "SHADOW"
    REPLAY_VALIDATED = "REPLAY_VALIDATED"
    POLICY_CHECKED = "POLICY_CHECKED"
    APPROVED_ACTIVE = "APPROVED_ACTIVE"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"

class GuardrailAuditRecord(BaseModel):
    schema_version: str = "1.0"
    guardrail_id: str = Field(..., description="Unique guardrail rule identifier")
    trace_id: str = Field(..., description="Active trace UUID for promotion context")
    lifecycle_state: GuardrailLifecycleState = Field(..., description="Active stage in security rule lifecycle")
    false_positive_rate: float = Field(..., ge=0.0, le=1.0, description="Observed shadow mode FP rate")
    logs_replayed: int = Field(..., ge=0, description="Count of historical log replays analyzed")
    policy_conflicts: int = Field(0, ge=0, description="Count of policy bundle conflicts detected")
    rollback_plan_id: Optional[str] = Field(None, description="Verification rollback identifier")
    evidence_pack_hash: Optional[str] = Field(None, description="Linked EvidencePack containing verification artifacts")
    promoted: bool = Field(False, description="True if promoted to approved active state")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BlastRadius(str, Enum):
    LOCAL = "local"
    SERVICE_GROUP = "service_group"
    GLOBAL = "global"

class ServiceRecoveryProfile(BaseModel):
    service_id: str = Field(..., description="Target service identifier")
    restart_safe: bool = Field(True, description="True if safe to restart programmatically")
    max_restart_attempts: int = Field(3, description="Maximum restart retries allowed")
    healthcheck_command: str = Field(..., description="Command to perform diagnostic validation")
    last_successful_healthcheck_at: datetime = Field(..., description="Last verified active timestamp")
    dependencies: List[str] = Field(default_factory=list, description="Services that must be online first")
    blast_radius: BlastRadius = Field(BlastRadius.LOCAL, description="Socio-technical impact classification")
    rollback_required: bool = Field(False, description="True if dynamic config rollback is needed upon failure")
    data_loss_risk: bool = Field(False, description="True if data disruption is possible")
    approval_required: bool = Field(False, description="True if high-risk approval is required")

class IncidentScope(str, Enum):
    LOCAL = "local"
    SERVICE_GROUP = "service_group"
    GLOBAL = "global"

class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    NON_COMPLIANT = "NON_COMPLIANT"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    NEEDS_REVIEW = "NEEDS_REVIEW"

# Structured import forwarders to avoid cyclic import issues
from rae_contracts.findings import AuditFinding

class ISOAuditRecord(BaseModel):
    schema_version: str = "1.0"
    iso_standard: str = "ISO-27001 / ISO-42001"
    control_id: str = Field(..., description="E.g., A.12.4.1 (Event logging)")
    evidence_source: str = Field(..., description="Linked MAES event trace_id")
    ledger_entries: List[str] = Field(..., description="List of validated sequence hashes")
    missing_evidence: List[str] = Field(default_factory=list, description="Detected chronological trace gaps")
    risk_exceptions: List[str] = Field(default_factory=list, description="Approved risk level bypasses")
    unresolved_quarantine_events: List[str] = Field(default_factory=list, description="Context blocks still in quarantine")
    compliance_status: ComplianceStatus = Field(..., description="Rigid evaluation status enum")
    findings: List[AuditFinding] = Field(default_factory=list, description="List of structured machine-actionable findings")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
