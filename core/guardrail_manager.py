import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from rae_contracts import (
    GuardrailAuditRecord, GuardrailLifecycleState, 
    AuditableEventType
)

logger = logging.getLogger(__name__)

class GuardrailManager:
    """
    Manages the lifecycle of security guardrails in RAE-Lab.
    Enforces a mandatory Shadow Mode period (72h) before promotion to active state.
    """
    def __init__(self, bridge):
        self.bridge = bridge
        self.shadow_threshold_hours = 72
        self.max_fp_rate = 0.001 # 0.1%

    async def register_candidate(self, trace_id: str, rule_definition: str) -> GuardrailAuditRecord:
        """Registers a new guardrail candidate for shadow testing."""
        record = GuardrailAuditRecord(
            guardrail_id=f"grd-{uuid.uuid4().hex[:8]}",
            trace_id=trace_id,
            lifecycle_state=GuardrailLifecycleState.CANDIDATE,
            false_positive_rate=0.0,
            logs_replayed=0,
            policy_conflicts=0,
            promoted=False
        )
        
        logger.info("guardrail_candidate_registered", guardrail_id=record.guardrail_id)
        self._log_audit_record(record, "Initial registration as candidate.")
        return record

    async def promote_to_shadow(self, record: GuardrailAuditRecord) -> GuardrailAuditRecord:
        """Promotes a candidate to shadow mode."""
        if record.lifecycle_state != GuardrailLifecycleState.CANDIDATE:
            raise ValueError("Only candidates can be promoted to shadow mode.")
            
        record.lifecycle_state = GuardrailLifecycleState.SHADOW
        record.created_at = datetime.now(timezone.utc) # Start shadow period
        
        logger.info("guardrail_promoted_to_shadow", guardrail_id=record.guardrail_id)
        self._log_audit_record(record, "Promoted to 72h Shadow Mode period.")
        return record

    async def evaluate_promotion(self, record: GuardrailAuditRecord, metrics: Dict[str, Any]) -> GuardrailAuditRecord:
        """
        Evaluates if a shadow guardrail is ready for full activation.
        Kryteria: 72h shadow, FP rate < 0.1%, 0 policy conflicts.
        """
        record.false_positive_rate = metrics.get("fp_rate", 1.0)
        record.logs_replayed = metrics.get("logs_replayed", 0)
        record.policy_conflicts = metrics.get("conflicts", 0)

        shadow_duration = datetime.now(timezone.utc) - record.created_at
        is_matured = shadow_duration >= timedelta(hours=self.shadow_threshold_hours)
        is_safe = record.false_positive_rate <= self.max_fp_rate
        no_conflicts = record.policy_conflicts == 0

        if is_matured and is_safe and no_conflicts:
            record.lifecycle_state = GuardrailLifecycleState.APPROVED_ACTIVE
            record.promoted = True
            logger.info("guardrail_promotion_successful", guardrail_id=record.guardrail_id)
            self._log_audit_record(record, "Promotion successful: Passed all safety and maturity gates.")
        else:
            reasons = []
            if not is_matured: reasons.append(f"Maturity gap: {shadow_duration.total_seconds()/3600:.1f}h / {self.shadow_threshold_hours}h")
            if not is_safe: reasons.append(f"High FP rate: {record.false_positive_rate:.4f} > {self.max_fp_rate}")
            if not no_conflicts: reasons.append(f"Policy conflicts: {record.policy_conflicts}")
            
            logger.warning("guardrail_promotion_denied", guardrail_id=record.guardrail_id, reasons=reasons)
            self._log_audit_record(record, f"Promotion denied: {'; '.join(reasons)}")

        return record

    def _log_audit_record(self, record: GuardrailAuditRecord, message: str):
        self.bridge.log_decision(
            action="guardrail_audit_log",
            reasoning=message,
            payload=record.dict()
        )
