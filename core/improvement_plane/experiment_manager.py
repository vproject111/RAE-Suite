import logging
from typing import Optional
from rae_core.models.improvement import Experiment
from core.improvement_plane.improvement_store import ImprovementStore

logger = logging.getLogger(__name__)

class ExperimentManager:
    """
    Manages creation and execution tracking of experiments.
    """
    def __init__(self, store: ImprovementStore):
        self.store = store

    def create_experiment(
        self, 
        experiment_id: str, 
        name: str, 
        hypothesis_id: str, 
        candidate: str, 
        success_criteria: str
    ) -> Experiment:
        e = Experiment(
            experiment_id=experiment_id,
            name=name,
            hypothesis_id=hypothesis_id,
            candidate=candidate,
            success_criteria=success_criteria
        )
        self.store.save_experiment(e)
        return e
