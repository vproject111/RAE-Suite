import logging
from typing import Optional
from rae_core.models.improvement import Hypothesis
from core.improvement_plane.improvement_store import ImprovementStore

logger = logging.getLogger(__name__)

class HypothesisManager:
    """
    Manages hypotheses for architectural and strategy improvements.
    """
    def __init__(self, store: ImprovementStore):
        self.store = store

    def create_hypothesis(self, hypothesis_id: str, statement: str, motivation: str, target_metric: str = "latency") -> Hypothesis:
        h = Hypothesis(
            hypothesis_id=hypothesis_id,
            statement=statement,
            motivation=motivation,
            target_metric=target_metric
        )
        self.store.save_hypothesis(h)
        return h

    def update_status(self, hypothesis_id: str, status: str) -> Optional[Hypothesis]:
        # Central model doesn't have status field, but we can update memory store tracking
        h = self.store.get_hypothesis(hypothesis_id)
        if h:
            logger.info(f"hypothesis_manager: Simulated status update of {hypothesis_id} to '{status}'")
            return h
        return None
