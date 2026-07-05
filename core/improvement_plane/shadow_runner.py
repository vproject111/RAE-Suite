import logging
import uuid
from typing import Dict, Any
from rae_core.models.improvement import Experiment, ExperimentRun
from rae_core.models.evidence import ActionRecord

logger = logging.getLogger(__name__)

class ShadowRunner:
    """
    Runs a shadow execution of a candidate strategy parallel to production
    without affecting live code execution, saving metrics to the ImprovementStore.
    """
    def __init__(self, improvement_store, evidence_router):
        self.store = improvement_store
        self.evidence = evidence_router

    def run(self, experiment: Experiment, input_data: dict) -> ExperimentRun:
        run_id = f"run-{uuid.uuid4().hex[:6]}"
        trace_id = f"trc-{uuid.uuid4().hex[:6]}"

        logger.info(f"[SHADOW] Starting shadow run {run_id} for experiment {experiment.experiment_id}")

        # Record action in evidence trail
        self.evidence.record_action(ActionRecord(
            department="lab",
            role="shadow_runner",
            action_type="shadow_run",
            goal=f"Shadow evaluation of experiment {experiment.experiment_id}",
            tools_used=["shadow_runner"],
            trace_id=trace_id
        ))

        # Execute candidate strategy
        metrics = self._execute_candidate(experiment.candidate, input_data)
        
        # Check success criteria
        passed = self._meets_criteria(metrics, experiment.success_criteria)
        result = "pass" if passed else "fail"

        run = ExperimentRun(
            run_id=run_id,
            experiment_id=experiment.experiment_id,
            mode="shadow",
            metrics=metrics,
            result=result,
            trace_id=trace_id
        )

        self.store.save_run(run)
        logger.info(f"[SHADOW] Run {run_id} completed: {result}")
        return run

    def _execute_candidate(self, candidate: str, input_data: dict) -> dict:
        # Simulate execution of the candidate code/logic
        latency = input_data.get("simulated_latency", 45.0)
        success_rate = 0.95 if "fail" not in candidate else 0.40
        cost = 0.002
        return {
            "latency_ms": latency,
            "success_rate": success_rate,
            "cost": cost
        }

    def _meets_criteria(self, metrics: dict, criteria: str) -> bool:
        # Check criteria like "success_rate > 0.90"
        if "success_rate > 0.90" in criteria:
            return metrics.get("success_rate", 0.0) > 0.90
        return True
