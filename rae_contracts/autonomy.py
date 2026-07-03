from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from rae_contracts.maes import RiskClass, ExecutionMode, RedactionStatus

# ==========================================
# ENUMY SYSTEMOWE (Typing Hardening)
# ==========================================

class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    QUARANTINE = "QUARANTINE"

class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SIMULATED_SUCCESS = "SIMULATED_SUCCESS"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    FAILED_ROLLBACK_REQUIRED = "FAILED_ROLLBACK_REQUIRED"
    FAILED_ESCALATED = "FAILED_ESCALATED"

class QualityStatus(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    QUARANTINE = "QUARANTINE"
    NOT_REQUIRED = "NOT_REQUIRED"

class MemoryWritebackStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BYPASSED = "BYPASSED"
    BLOCKED = "BLOCKED"

class DistanceMetric(str, Enum):
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"

class NetworkPolicy(str, Enum):
    DENY_ALL = "deny_all"
    ALLOW_WHITELISTED = "allow_whitelisted"
    SANDBOX_ONLY = "sandbox_only"

class TaskState(str, Enum):
    RECEIVED = "RECEIVED"
    CLASSIFIED = "CLASSIFIED"
    POLICY_CHECKED = "POLICY_CHECKED"
    CAPABILITY_CHECKED = "CAPABILITY_CHECKED"
    PLANNED = "PLANNED"
    DRY_RUN = "DRY_RUN"
    SANDBOX_EXECUTING = "SANDBOX_EXECUTING"
    VERIFYING = "VERIFYING"
    QUALITY_GATE = "QUALITY_GATE"
    EVIDENCE_PACKING = "EVIDENCE_PACKING"
    LEDGER_COMMIT = "LEDGER_COMMIT"
    MEMORY_WRITEBACK = "MEMORY_WRITEBACK"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    FAILED_ROLLBACK_REQUIRED = "FAILED_ROLLBACK_REQUIRED"
    FAILED_ESCALATED = "FAILED_ESCALATED"

# ==========================================
# SCHEMATY DANYCH KONTRAKTÓW
# ==========================================

class EmbeddingProfile(BaseModel):
    schema_version: str = "1.0"
    id: str = Field(..., description="Unique profile identifier")
    provider: str = Field(..., description="API provider, e.g., 'ollama', 'openai'")
    model: str = Field(..., description="Model name, e.g., 'qwen-embed'")
    dimension: int = Field(..., gt=0, description="Vector dimensionality, e.g., 768")
    distance: DistanceMetric = Field(DistanceMetric.COSINE)
    normalization: str = Field("l2", description="Vector normalization type")
    model_hash: Optional[str] = None
    tokenizer_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True

class CapabilityContract(BaseModel):
    schema_version: str = "1.0"
    contract_id: str
    allowed_risk_classes: List[RiskClass]
    allowed_tools: List[str]
    denied_tools: List[str]
    outbound_network_policy: NetworkPolicy = Field(NetworkPolicy.DENY_ALL)
    secret_access_allowlist: List[str]
    max_token_budget: int = Field(..., gt=0)
    max_execution_time_seconds: int = Field(..., gt=0)

class PolicyBundle(BaseModel):
    schema_version: str = "1.0"
    bundle_id: str
    version: str
    bundle_hash: str = Field(..., description="SHA-256 hash of the entire bundle contents")
    valid_from: datetime
    valid_to: Optional[datetime] = None
    risk_matrix_version: str
    capability_contract_version: str
    secret_policy_version: str
    quality_gate_profile: str

class RiskAssessment(BaseModel):
    schema_version: str = "1.0"
    assessment_id: str
    trace_id: str
    risk_class: RiskClass
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence of classifier [0.0-1.0]")
    reasons: List[str] = Field(..., description="Logical path audit reasons")
    detected_sensitive_assets: List[str] = Field(default_factory=list, description="List of matched sensitive files or tables")
    requires_human_review: bool = False
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DecisionLedgerEntry(BaseModel):
    schema_version: str = "1.0"
    ledger_entry_id: str
    trace_id: str
    risk_class: RiskClass
    decision: DecisionType
    execution_mode: ExecutionMode = Field(ExecutionMode.LIVE)
    evidence_pack_hash: str = Field(..., description="SHA-256 hash of the zipped ISO Evidence Pack")
    evidence_pack_uri: str = Field(..., description="Storage URI of the Evidence Pack")
    policy_bundle_hash: str = Field(..., description="Active Policy Bundle hash used for the decision")
    signed_by: str = Field("rae-autonomy-kernel", description="Signature identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QualityGateResult(BaseModel):
    schema_version: str = "1.0"
    status: QualityStatus
    existing_tests_passed: bool
    generated_tests_passed: Optional[bool] = None
    coverage_before: Optional[float] = Field(None, ge=0.0, le=100.0)
    coverage_after: Optional[float] = Field(None, ge=0.0, le=100.0)
    mutation_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    critical_vulnerabilities: int = Field(0, ge=0)
    high_vulnerabilities: int = Field(0, ge=0)
    architecture_violations: int = Field(0, ge=0)
    test_integrity_passed: bool
    report_uri: Optional[str] = None

class EvidencePack(BaseModel):
    schema_version: str = "1.0"
    evidence_pack_id: str
    trace_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    artifacts: Dict[str, str] = Field(default_factory=dict, description="E.g. {'sast_report': 'sha256...'}")
    logs_uri: Optional[str] = None
    quality_report_uri: Optional[str] = None
    dry_run_report_uri: Optional[str] = None
    vulnerability_report_uri: Optional[str] = None
    hash_sha256: str
    retention_until: datetime
    redaction_status: RedactionStatus = RedactionStatus.REDACTED

class ApprovalPack(BaseModel):
    schema_version: str = "1.0"
    approval_pack_id: str
    trace_id: str
    risk_class: RiskClass
    action_plan: str
    expected_impact: str
    dry_run_output_uri: str
    rollback_plan_id: str
    quality_gate_result_id: str
    safer_alternatives: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RollbackPlan(BaseModel):
    schema_version: str = "1.0"
    rollback_plan_id: str
    trace_id: str
    risk_class: RiskClass
    strategy: str
    snapshot_uri: Optional[str] = None
    commands: List[str] = Field(default_factory=list, description="List of safe recovery command steps")
    verification_steps: List[str] = Field(default_factory=list, description="List of verification assertions")
    estimated_recovery_time_seconds: Optional[int] = Field(None, gt=0)
    tested: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StateTransition(BaseModel):
    schema_version: str = "1.0"
    from_state: TaskState
    to_state: TaskState
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: Optional[str] = None
    actor: str = Field(..., description="Agent or module triggering state change")

class ExecutionReceipt(BaseModel):
    schema_version: str = "1.0"
    receipt_id: str
    goal_id: str
    task_id: str
    trace_id: str
    module: str = Field(..., description="Module name, e.g., 'rae-hive'")
    agent_id: str = Field(..., description="Agent identifier executing the task")
    risk_class: RiskClass
    capability_contract_id: str
    policy_decision: DecisionType
    execution_status: ExecutionStatus
    quality_status: QualityStatus
    execution_mode: ExecutionMode = Field(ExecutionMode.LIVE)
    sandbox_id: Optional[str] = None
    worktree_id: Optional[str] = None
    rollback_plan_id: Optional[str] = None
    evidence_pack_hash: str
    ledger_entry_id: str
    memory_writeback_status: MemoryWritebackStatus
    final_state: TaskState
    state_transitions: List[StateTransition] = Field(default_factory=list)
    llm_provider: str
    llm_model: str
    prompt_template_version: str
    tool_versions: Dict[str, str] = Field(default_factory=dict, description="E.g. {'pytest': '8.2.0'}")
    started_at: datetime
    finished_at: datetime

class ContextEnvelope(BaseModel):
    schema_version: str = "1.0"
    context_id: str
    source_type: str = Field("memory", description="Source indicator, e.g. 'memory', 'file', 'user'")
    source_uri: str
    source_hash: str
    trust_score: float = Field(0.5, ge=0.0, le=1.0)
    information_class: str = Field("internal", description="public, internal, confidential, restricted")
    tenant_id: str
    project_id: str
    memory_layer: str = Field("working", description="sensory, episodic, working, semantic, long_term, reflective")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime
    token_cost: int = 0
    retrieved_content: str
    allowed_uses: List[str] = Field(default_factory=list)

class WorkflowStep(BaseModel):
    step_id: str
    capability: str
    required_risk_class: RiskClass = RiskClass.R1
    timeout_seconds: int = 120

class WorkflowDefinition(BaseModel):
    schema_version: str = "1.0"
    workflow_id: str
    name: str
    version: str
    entry_conditions: Dict[str, Any] = Field(default_factory=dict)
    steps: List[WorkflowStep]
    exit_conditions: Dict[str, Any] = Field(default_factory=dict)
    rollback_workflow_id: Optional[str] = None

class HandoffEnvelope(BaseModel):
    schema_version: str = "1.0"
    handoff_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    source_module: str
    target_module: str
    required_capabilities: List[str] = Field(default_factory=list)
    restricted_context_pack: Dict[str, Any] = Field(default_factory=dict)
    input_artifacts: List[str] = Field(default_factory=list)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    token_budget: int = 50000
    timeout_seconds: int = 300
    information_class: str = "internal"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


