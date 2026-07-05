import time
import logging
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class CandidateGuardrail(BaseModel):
    guardrail_id: str
    pattern: str
    error_message: str
    created_at: float = Field(default_factory=time.time)
    hits: int = 0
    false_positives: int = 0
    is_shadow: bool = True

class ShadowModelStats(BaseModel):
    candidate_model_name: str
    total_evaluations: int = 0
    semantic_matches: int = 0
    promoted: bool = False

class ShadowEvaluator:
    """
    Implements Failure Mining, Shadow Model Evaluation, and Cold-Path Distillation.
    Runs defensive guardrails in Shadow Mode on the Adaptive Improvement Lane.
    """
    def __init__(self):
        self.candidate_guardrails: Dict[str, CandidateGuardrail] = {}
        self.shadow_model_stats: Dict[str, ShadowModelStats] = {}
        self.distillation_backlog: Dict[str, int] = {}  # task_pattern -> hit_count

    # 1. Failure Mining & Shadow Mode Guardrails
    def mine_failure(self, error_message: str, pattern: str) -> str:
        """
        Creates a new candidate guardrail in Shadow Mode from failed error traces.
        """
        guardrail_id = f"grd-{int(time.time())}"
        self.candidate_guardrails[guardrail_id] = CandidateGuardrail(
            guardrail_id=guardrail_id,
            pattern=pattern,
            error_message=f"Defensive block: {error_message}"
        )
        logger.info(f"shadow_evaluator: Mined failure. Created shadow guardrail {guardrail_id} for pattern '{pattern}'")
        return guardrail_id

    def evaluate_shadow_guardrails(self, payload_text: str) -> List[str]:
        """
        Runs shadow guardrails in the background. Tracks hits and false positives.
        Does not raise active exceptions (Shadow Mode / Dry Run).
        """
        alerts = []
        for g_id, guard in self.candidate_guardrails.items():
            if guard.pattern in payload_text:
                guard.hits += 1
                logger.info(f"shadow_evaluator: Shadow guardrail {g_id} matched payload text. (Hits: {guard.hits})")
                alerts.append(guard.error_message)
        return alerts

    def promote_guardrail(self, guardrail_id: str, age_hours: float, max_false_positive_rate: float = 0.001) -> bool:
        """
        Promotes a shadow guardrail to active production lane.
        Requires >= 72 hours age and false positive rate < 0.1%.
        """
        if guardrail_id not in self.candidate_guardrails:
            return False
            
        guard = self.candidate_guardrails[guardrail_id]
        fp_rate = (guard.false_positives / guard.hits) if guard.hits > 0 else 0.0
        
        if age_hours >= 72.0 and fp_rate < max_false_positive_rate:
            guard.is_shadow = False
            logger.info(f"shadow_evaluator: Promoted guardrail {guardrail_id} to active production lane. (FP rate: {fp_rate:.4f})")
            return True
        return False

    # 2. Shadow Model Evaluation
    def record_shadow_evaluation(self, candidate_model: str, is_semantic_match: bool):
        """
        Logs a shadow model evaluation against production outcomes.
        Marks for promotion after 50,000 matches.
        """
        if candidate_model not in self.shadow_model_stats:
            self.shadow_model_stats[candidate_model] = ShadowModelStats(candidate_model_name=candidate_model)
            
        stats = self.shadow_model_stats[candidate_model]
        stats.total_evaluations += 1
        if is_semantic_match:
            stats.semantic_matches += 1
            
        # Target: 50,000 samples
        if stats.total_evaluations >= 50000 and (stats.semantic_matches / stats.total_evaluations >= 0.98):
            stats.promoted = True
            logger.info(f"shadow_evaluator: Promoted candidate model {candidate_model} to production! (Matches: {stats.semantic_matches}/50000)")

    # 3. Cold-Path Distillation
    def track_cold_path(self, task_reasoning_pattern: str):
        """
        Tracks repetitive reasoning traces from long-tail tasks for local distillation.
        """
        self.distillation_backlog[task_reasoning_pattern] = self.distillation_backlog.get(task_reasoning_pattern, 0) + 1
        hits = self.distillation_backlog[task_reasoning_pattern]
        
        # If pattern hits often (e.g. > 100 times), mark for distillation
        if hits >= 100:
            logger.warning(f"shadow_evaluator: Task pattern '{task_reasoning_pattern}' hit {hits} times. Recommended for distillation (int8 quantization).")
