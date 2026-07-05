import logging
from typing import List
from core.models.improvement import ImprovementProposal, PromotionDecision, ExperimentRun

logger = logging.getLogger(__name__)

class PromotionGate:
    """
    Evaluates improvement proposals before promoting them to the Stable Lane.
    Requires shadow runs to pass, rollback plan to exist, and Auditor approval.
    """
    def __init__(self, auditor_engine, improvement_store):
        self.auditor = auditor_engine
        self.store = improvement_store

    def evaluate(self, proposal: ImprovementProposal) -> PromotionDecision:
        failures = []

        runs: List[ExperimentRun] = self.store.get_runs_for(proposal.experiment_id)
        shadow_runs = [r for r in runs if r.mode == "shadow"]

        # 1. Check if shadow run exists
        if not shadow_runs:
            failures.append("has_shadow_run: Brak shadow run.")

        # 2. Check if shadow runs passed
        if shadow_runs and not any(r.result == "pass" for r in shadow_runs):
            failures.append("shadow_passed: Żaden shadow run nie przeszedł.")

        # 3. Check if rollback plan exists in requirements
        if not proposal.promotion_requirements or "rollback_plan" not in proposal.promotion_requirements:
            failures.append("has_rollback_plan: Brak planu rollback.")

        # 4. Check if Auditor approved
        if not self.auditor.can_promote(proposal.proposal_id):
            failures.append("auditor_approved: Brak zatwierdzonego werdyktu Auditora.")

        if failures:
            logger.warning(f"Promotion BLOCKED for {proposal.proposal_id}: {failures}")
            return PromotionDecision(
                proposal_id=proposal.proposal_id,
                approved=False,
                reason="; ".join(failures)
            )

        logger.info(f"Promotion APPROVED for {proposal.proposal_id}")
        return PromotionDecision(
            proposal_id=proposal.proposal_id,
            approved=True,
            reason="All gates passed."
        )
