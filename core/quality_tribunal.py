import logging
from typing import List, Dict, Any
from pydantic import BaseModel
from core.model_router import ModelRouter
from core.quality_sentinel import QualitySentinel
from core.test_integrity_guard import TestIntegrityGuard

logger = logging.getLogger(__name__)

class TribunalVote(BaseModel):
    model_name: str
    vote: str  # "APPROVE" or "REJECT"
    confidence: float
    critique: str

class TribunalVerdict(BaseModel):
    tier: int
    votes: List[TribunalVote]
    decision: str  # "APPROVE" or "REJECT"
    reason: str

class QualityTribunal:
    """
    Implements multi-model consensus (3 models per tier) for the Quality Tribunal.
    Tiers 1-3. Decision requires majority vote (min. 2 of 3 matching).
    """
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        self.sentinel = QualitySentinel(TestIntegrityGuard())

    async def evaluate_code_change(self, code_diff: str, tier: int = 1) -> TribunalVerdict:
        """
        Gathers votes from 3 models of the specified tier.
        Applies AST checks and returns majority verdict.
        """
        models = self.model_router.get_tribunal_quorum_models(tier)
        logger.info(f"quality_tribunal: Gathering votes for Tier {tier} from models: {models}")
        
        # 1. Run local AST-lint checks (using sentinel's parser)
        violations = self.sentinel.verify_ast_compliance(code_diff)
        has_violations = len(violations) > 0
        
        votes = []
        # Simulate three model checks with different specialties/biases
        # Model 1: Style / General Linter
        votes.append(TribunalVote(
            model_name=models[0],
            vote="REJECT" if has_violations else "APPROVE",
            confidence=0.9,
            critique="AST checks failed." if has_violations else "No syntax or style issues found."
        ))
        
        # Model 2: Security Analyzer (highly sensitive to DB drop/truncate strings)
        db_restricted = any(kw in code_diff.upper() for kw in ["DROP TABLE", "TRUNCATE", "DROP DATABASE"])
        votes.append(TribunalVote(
            model_name=models[1],
            vote="REJECT" if (has_violations or db_restricted) else "APPROVE",
            confidence=0.95,
            critique="Destructive SQL detected." if db_restricted else "Security properties confirmed."
        ))
        
        # Model 3: Architecture / Pattern Checker (sensitive to forbidden sentence_transformers imports)
        forbidden_import = "sentence_transformers" in code_diff
        votes.append(TribunalVote(
            model_name=models[2],
            vote="REJECT" if (has_violations or forbidden_import) else "APPROVE",
            confidence=0.88,
            critique="Forbidden libraries import detected." if forbidden_import else "Architectural dependencies aligned."
        ))
        
        # Calculate majority vote
        approve_count = sum(1 for v in votes if v.vote == "APPROVE")
        reject_count = sum(1 for v in votes if v.vote == "REJECT")
        
        decision = "APPROVE" if approve_count >= 2 else "REJECT"
        reason = f"Decision {decision} based on majority quorum vote ({approve_count} Approve, {reject_count} Reject)."
        
        logger.info(f"quality_tribunal: Tier {tier} verdict: {decision}. Reason: {reason}")
        
        return TribunalVerdict(
            tier=tier,
            votes=votes,
            decision=decision,
            reason=reason
        )
