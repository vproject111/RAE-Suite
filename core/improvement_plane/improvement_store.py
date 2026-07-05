import logging
from typing import Dict, List, Optional
from core.models.improvement import Hypothesis, Experiment, ExperimentRun

logger = logging.getLogger(__name__)

class ImprovementStore:
    """
    In-memory / local persistent store for Hypothesis, Experiment, and ExperimentRun models.
    """
    def __init__(self):
        self._hypotheses: Dict[str, Hypothesis] = {}
        self._experiments: Dict[str, Experiment] = {}
        self._runs: Dict[str, ExperimentRun] = {}

    def save_hypothesis(self, h: Hypothesis):
        self._hypotheses[h.hypothesis_id] = h
        logger.info(f"improvement_store: Saved hypothesis {h.hypothesis_id} ({h.name})")

    def get_hypothesis(self, h_id: str) -> Optional[Hypothesis]:
        return self._hypotheses.get(h_id)

    def save_experiment(self, e: Experiment):
        self._experiments[e.experiment_id] = e
        logger.info(f"improvement_store: Saved experiment {e.experiment_id} ({e.name})")

    def get_experiment(self, e_id: str) -> Optional[Experiment]:
        return self._experiments.get(e_id)

    def save_run(self, r: ExperimentRun):
        self._runs[r.run_id] = r
        logger.info(f"improvement_store: Saved run {r.run_id} (result: {r.result})")

    def get_runs_for(self, experiment_id: str) -> List[ExperimentRun]:
        return [r for r in self._runs.values() if r.experiment_id == experiment_id]
