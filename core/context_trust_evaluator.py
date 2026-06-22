import logging
from typing import Dict, Any, List, Tuple
from rae_contracts import RiskClass

logger = logging.getLogger(__name__)

class ContextTrustEvaluator:
    """
    Evaluates and scores retrieved historical context for RAE-Suite.
    Protects against memory poisoning by enforcing trust thresholds.
    """
    def __init__(self):
        self.reject_threshold = 0.4
        self.advisory_threshold = 0.7

    def evaluate_trust(self, memory_metadata: Dict[str, Any]) -> Tuple[float, str]:
        """
        Calculates a trust score (0.0-1.0) based on source, success rate, and risk links.
        Returns: (trust_score, classification)
        """
        # Base score
        score = 0.5
        
        # 1. Source Layer Weighting
        layer = memory_metadata.get("layer", "episodic")
        if layer == "semantic": score += 0.2 # Verified facts
        elif layer == "reflective": score += 0.1 # Lessons learned
        elif layer == "working": score -= 0.1 # Volatile context
        
        # 2. Success History
        success_rate = memory_metadata.get("historical_success_rate", 0.5)
        score += (success_rate - 0.5) * 0.4
        
        # 3. Risk Class Isolation
        risk_class = memory_metadata.get("risk_class", "R0")
        if risk_class in ["R5", "R6"]:
            score -= 0.3 # Penalize high-risk associated memories
            
        # 4. Quarantine Check
        if memory_metadata.get("quarantined", False):
            score = 0.0 # Absolute rejection
            
        # Clamp score
        score = max(0.0, min(1.0, score))
        
        # Determine Classification
        classification = "REJECTED"
        if score >= self.advisory_threshold:
            classification = "USABLE_PLANNING_INPUT"
        elif score >= self.reject_threshold:
            classification = "ADVISORY_ONLY"
        else:
            classification = "REJECTED"
            
        logger.info("context_trust_evaluated", score=score, classification=classification)
        return score, classification

    def filter_context(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters out untrusted memories."""
        filtered = []
        for mem in memories:
            score, classification = self.evaluate_trust(mem)
            if classification != "REJECTED":
                mem["trust_score"] = score
                mem["trust_classification"] = classification
                filtered.append(mem)
        return filtered
