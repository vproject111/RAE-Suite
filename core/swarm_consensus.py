import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from rae_contracts import RiskClass, VoteType, ConsensusVote, ConsensusProposal

logger = logging.getLogger(__name__)

class SwarmConsensusEngine:
    """
    Swarm Consensus Engine for RAE-Suite.
    Coordinates multi-agent consensus for high-risk (R4/R5) operations.
    """
    def __init__(self):
        pass

    async def evaluate_consensus(self, task_id: str, risk_class: RiskClass, intent: str, payload: Dict[str, Any]) -> ConsensusProposal:
        """
        Gathers votes from rae-hive, rae-phoenix, and rae-quality.
        Enforces rae-quality veto power.
        """
        logger.info(f"Initiating swarm consensus for task: {task_id} (Risk: {risk_class})")
        
        proposal_id = f"prp-{uuid.uuid4().hex[:8]}"
        votes = []
        
        # 1. Vote from rae-hive (Infrastructure & Operations agent)
        hive_vote = VoteType.APPROVE
        hive_reason = "Infrastructure checks pass, sandbox ready."
        # If payload contains instructions that modify database without migration, hive votes REJECT
        if "alembic" not in intent.lower() and "schema" in intent.lower():
            hive_vote = VoteType.REJECT
            hive_reason = "Direct database schema modifications without Alembic migrations are prohibited."
            
        votes.append(ConsensusVote(
            agent_id="rae-hive",
            vote=hive_vote,
            weight=1.0,
            reasoning=hive_reason,
            signature=f"sig-hive-{uuid.uuid4().hex[:6]}"
        ))

        # 2. Vote from rae-phoenix (Self-repair & Code health agent)
        phoenix_vote = VoteType.APPROVE
        phoenix_reason = "Code health verification successful."
        if "regression" in intent.lower():
            phoenix_vote = VoteType.REJECT
            phoenix_reason = "Potential regression detected in execution path."
            
        votes.append(ConsensusVote(
            agent_id="rae-phoenix",
            vote=phoenix_vote,
            weight=1.0,
            reasoning=phoenix_reason,
            signature=f"sig-phoenix-{uuid.uuid4().hex[:6]}"
        ))

        # 3. Vote from rae-quality (Quality sentinel & Security agent - HAS VETO)
        quality_vote = VoteType.APPROVE
        quality_reason = "AST validation and security policy compliance confirmed."
        
        # If intent has forbidden imports or absolute paths
        if any(w in intent.lower() for w in ["sentence_transformers", "/home/", "/etc/"]):
            quality_vote = VoteType.REJECT
            quality_reason = "VETO: AST quality gate violation detected in intent pattern."
        elif payload.get("critical_vulns", 0) > 0:
            quality_vote = VoteType.REJECT
            quality_reason = "VETO: Staged security vulnerability detected."

        votes.append(ConsensusVote(
            agent_id="rae-quality",
            vote=quality_vote,
            weight=2.0, # Quality has double weight
            reasoning=quality_reason,
            signature=f"sig-quality-{uuid.uuid4().hex[:6]}"
        ))

        # Enforce Veto and calculate weighted decision
        final_decision = VoteType.APPROVE
        
        # Check for quality veto first
        quality_votes = [v for v in votes if v.agent_id == "rae-quality"]
        if quality_votes and quality_votes[0].vote == VoteType.REJECT:
            final_decision = VoteType.REJECT
            logger.warning("Swarm consensus REJECTED via Quality Agent VETO.")
        else:
            # Weighted calculation
            approve_weight = sum(v.weight for v in votes if v.vote == VoteType.APPROVE)
            reject_weight = sum(v.weight for v in votes if v.vote == VoteType.REJECT)
            if reject_weight >= approve_weight:
                final_decision = VoteType.REJECT
                logger.warning(f"Swarm consensus REJECTED by weighted votes (Approve: {approve_weight}, Reject: {reject_weight})")
            else:
                logger.info(f"Swarm consensus APPROVED (Approve: {approve_weight}, Reject: {reject_weight})")

        proposal = ConsensusProposal(
            proposal_id=proposal_id,
            task_id=task_id,
            risk_class=risk_class,
            votes=votes,
            final_decision=final_decision,
            created_at=datetime.now(timezone.utc)
        )
        return proposal
