import logging
from typing import Dict, Any
from rae_core.models.improvement import RollbackDecision

logger = logging.getLogger(__name__)

class CanaryManager:
    """
    Manages limited-exposure canary rollouts of candidate strategies.
    Triggers automatic rollbacks when anomaly thresholds or error rates are exceeded.
    """
    def __init__(self, error_rate_threshold: float = 0.05):
        self.error_rate_threshold = error_rate_threshold

    def evaluate_canary_health(self, experiment_id: str, canary_metrics: Dict[str, Any]) -> RollbackDecision:
        """
        Evaluates metrics from a live canary run.
        Triggers auto-rollback if error_rate > threshold.
        """
        error_rate = canary_metrics.get("error_rate", 0.0)
        logger.info(f"canary_manager: Checking health for experiment {experiment_id}. Canary error rate: {error_rate:.4f} (Threshold: {self.error_rate_threshold})")
        
        if error_rate > self.error_rate_threshold:
            reason = f"Canary error rate {error_rate:.4f} exceeded threshold {self.error_rate_threshold}."
            logger.warning(f"canary_manager: AUTO-ROLLBACK TRIGGERED: {reason}")
            return RollbackDecision(
                proposal_id=f"can-{experiment_id}",
                rollback_triggered=True,
                reason=reason
            )
            
        return RollbackDecision(
            proposal_id=f"can-{experiment_id}",
            rollback_triggered=False,
            reason="Canary metrics are healthy."
        )
