import logging
from typing import Optional
from core.models.improvement import Hypothesis
from core.improvement_plane.improvement_store import ImprovementStore

logger = logging.getLogger(__name__)

class HypothesisManager:
    """
    Manages hypotheses for architectural and strategy improvements.
    """
    def __init__(self, store: ImprovementStore):
        self.store = store

    def create_hypothesis(self, hypothesis_id: str, name: str, description: str) -> Hypothesis:
        h = Hypothesis(
            hypothesis_id=hypothesis_id,
            name=name,
            description=description,
            status="draft"
        )
        self.store.save_hypothesis(h)
        return h

    def update_status(self, hypothesis_id: str, status: str) -> Optional[Hypothesis]:
        h = self.store.get_hypothesis(hypothesis_id)
        if h:
            h.status = status
            self.store.save_hypothesis(h)
            logger.info(f"hypothesis_manager: Updated hypothesis {hypothesis_id} status to '{status}'")
            return h
        return None
