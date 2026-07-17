import logging
from typing import Dict, Any, List, Tuple
from rae_contracts import RiskClass, ContextEnvelope

logger = logging.getLogger(__name__)

class ContextTrustEvaluator:
    """
    Evaluates and scores retrieved historical context for RAE-Suite.
    Protects against memory poisoning by enforcing trust thresholds.
    """
    def __init__(self):
        import os
        try:
            self.reject_threshold = float(os.getenv("RAE_CONTEXT_REJECT_THRESHOLD", "0.4"))
        except ValueError:
            logger.error("Invalid RAE_CONTEXT_REJECT_THRESHOLD env value; fallback to 0.4")
            self.reject_threshold = 0.4

        try:
            self.advisory_threshold = float(os.getenv("RAE_CONTEXT_ADVISORY_THRESHOLD", "0.7"))
        except ValueError:
            logger.error("Invalid RAE_CONTEXT_ADVISORY_THRESHOLD env value; fallback to 0.7")
            self.advisory_threshold = 0.7

    def evaluate_trust(self, memory_metadata: Dict[str, Any]) -> Tuple[float, str]:
        """
        Calculates a trust score (0.0-1.0) based on source, success rate, and risk links.
        Returns: (trust_score, classification)
        """
        # Strict Isolation of RESTRICTED data (Phase 3 Enforcement Contract)
        # Check this first so it bypasses quarantine and other factors completely
        info_class = memory_metadata.get("information_class", "internal").lower()
        layer = memory_metadata.get("layer", "episodic")
        if info_class == "restricted" and layer != "working":
            logger.warning("RESTRICTED data isolation violation: rejected due to layer placement.")
            return 0.0, "REJECTED"

        # Base score
        score = 0.5
        
        # 1. Source Layer Weighting
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
        is_quarantined = memory_metadata.get("quarantined", False) or memory_metadata.get("quarantine_status", False) or memory_metadata.get("quarantine", False)
        if is_quarantined:
            score = 0.5
            
        # Clamp score
        score = max(0.0, min(1.0, score))
        
        # Determine Classification
        if is_quarantined:
            classification = "ADVISORY_ONLY"
        elif score >= self.advisory_threshold:
            classification = "USABLE_PLANNING_INPUT"
        elif score >= self.reject_threshold:
            classification = "ADVISORY_ONLY"
        else:
            classification = "REJECTED"
            
        logger.info(f"Context trust evaluated: score={score:.2f}, classification={classification}")
        return score, classification

    def filter_context(self, memories: List[Dict[str, Any]]) -> List[ContextEnvelope]:
        """Filters out untrusted memories and returns sorted ContextEnvelopes."""
        import uuid
        from datetime import datetime, timezone, timedelta
        
        filtered = []
        for mem in memories:
            score, classification = self.evaluate_trust(mem)
            if classification != "REJECTED":
                # Resolve timestamps
                created_at = mem.get("created_at")
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at)
                    except ValueError:
                        created_at = datetime.now(timezone.utc)
                elif not isinstance(created_at, datetime):
                    created_at = datetime.now(timezone.utc)
                    
                envelope = ContextEnvelope(
                    context_id=mem.get("context_id", f"ctx-{uuid.uuid4().hex[:8]}"),
                    source_type=mem.get("source_type", "memory"),
                    source_uri=mem.get("source_uri", "rae://memory/unspecified"),
                    source_hash=mem.get("source_hash", "n/a"),
                    trust_score=score,
                    information_class=mem.get("information_class", "internal"),
                    tenant_id=mem.get("tenant_id", "default-tenant"),
                    project_id=mem.get("project_id", "default-project"),
                    memory_layer=mem.get("layer", "working"),
                    created_at=created_at,
                    valid_until=datetime.now(timezone.utc) + timedelta(hours=24),
                    retrieved_content=mem.get("content", ""),
                    allowed_uses=mem.get("allowed_uses", [])
                )
                filtered.append(envelope)
                
        # Sort context envelopes by trust score descending (Potok selekcji)
        filtered.sort(key=lambda x: x.trust_score, reverse=True)
        return filtered

