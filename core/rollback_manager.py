import logging
from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class IncidentScope(str, Enum):
    LOCAL = "local"
    SERVICE_GROUP = "service_group"
    GLOBAL = "global"

class RollbackPlan(BaseModel):
    plan_id: str
    action_type: str  # container_restart | config_restore | git_worktree_revert | db_schema_rollback
    sla_threshold_seconds: float
    verified_in_sandbox: bool = False

class RollbackSLAManager:
    """
    Manages recovery guarantees based on operational complexity (Differentiated SLA Matrix).
    Verifies rollback plans against SLA bounds and tracks incident scopes.
    """
    SLA_MATRIX: Dict[str, float] = {
        "container_restart": 15.0,
        "git_worktree_revert": 30.0,
        "config_restore": 60.0,
        "db_schema_rollback": 120.0,
        "vector_projection_rollback": 300.0
    }

    def __init__(self):
        self.quarantined_contexts: Dict[str, IncidentScope] = {}

    def get_max_allowed_sla(self, action_type: str) -> float:
        return self.SLA_MATRIX.get(action_type, 30.0)

    def verify_plan(self, plan: RollbackPlan, risk_class: str) -> bool:
        """
        No R4/R5 action can be approved unless its corresponding RollbackPlan
        has been successfully tested in a sandbox environment and fits its target SLA bounds.
        """
        max_allowed = self.get_max_allowed_sla(plan.action_type)
        
        # Check SLA bounds
        if plan.sla_threshold_seconds > max_allowed:
            logger.warning(f"RollbackPlan {plan.plan_id} SLA {plan.sla_threshold_seconds}s exceeds max allowed {max_allowed}s for {plan.action_type}")
            return False

        # If risk is R4/R5, require sandbox verification
        if risk_class in ["R4", "R5"] and not plan.verified_in_sandbox:
            logger.warning(f"RollbackPlan {plan.plan_id} for high risk {risk_class} has not been verified in sandbox.")
            return False

        logger.info(f"RollbackPlan {plan.plan_id} VERIFIED (SLA limit: {plan.sla_threshold_seconds}s)")
        return True

    def quarantine_incident(self, context_id: str, scope: IncidentScope) -> List[str]:
        """
        Quarantines affected contexts based on incident scope to prevent global suite freezes.
        """
        self.quarantined_contexts[context_id] = scope
        logger.warning(f"Incident quarantined: context {context_id} under scope '{scope.value}'")
        
        if scope == IncidentScope.LOCAL:
            return [context_id]
        elif scope == IncidentScope.SERVICE_GROUP:
            # Quarantine the target and related mock service group contexts
            return [context_id, f"{context_id}_dep1", f"{context_id}_dep2"]
        else: # IncidentScope.GLOBAL
            return ["all_active_contexts"]
