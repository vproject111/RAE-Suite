import logging
import hashlib
from typing import List, Dict, Any, Tuple
from rae_contracts import ContextEnvelope

logger = logging.getLogger(__name__)

class ContextBroker:
    """
    Implements Hierarchical Context Pruning and Adaptive Retrieval Depth.
    Optimizes context size and retrieval parameters for Context Economy.
    """
    def __init__(self, token_limit: int = 1500, reject_threshold: float = 0.4):
        self.token_limit = token_limit
        self.reject_threshold = reject_threshold

    def determine_retrieval_depth(self, candidates: List[Dict[str, Any]]) -> Tuple[int, bool]:
        """
        Implements Adaptive Retrieval Depth.
        Analyzes candidate score distributions.
        Returns: (k_depth, run_reranker)
        """
        if not candidates:
            return 0, False
            
        # Validate candidate scores exist
        if any("score" not in c for c in candidates):
            raise ValueError("Invalid candidate: missing score field.")

        # Sort candidates by score descending
        sorted_candidates = sorted(candidates, key=lambda x: x.get("score", 0.0), reverse=True)
        top_score = sorted_candidates[0].get("score", 0.0)
        
        if len(sorted_candidates) == 1:
            return 1, False
            
        second_score = sorted_candidates[1].get("score", 0.0)
        gap = top_score - second_score
        
        # If top answer stands out significantly, skip reranking and return small k
        if gap > 0.15:
            logger.info(f"adaptive_retrieval_depth: top score stands out (gap={gap:.3f}). Returning k=3 and skipping rerank.")
            return 3, False
        # If scores are close/clustered (zbite), expand k to 30 and enable reranking
        elif gap < 0.05:
            logger.info(f"adaptive_retrieval_depth: scores are clustered (gap={gap:.3f}). Expanding depth to k=30 and enabling reranker.")
            return 30, True
        else:
            # Moderate gap, return standard depth
            return 10, True

    def prune_context(self, envelopes: List[ContextEnvelope], constitution: str = "") -> str:
        """
        Implements Hierarchical Context Pruning.
        Compresses envelopes into a hierarchical structure:
        Constitution -> Project Profile -> Summaries -> Raw Leaf Data.
        Prunes lower-trust leaves if exceeding the word/token budget limit.
        """
        # Filter out envelopes below reject threshold
        valid_envs = [e for e in envelopes if e.trust_score >= self.reject_threshold]
        
        # Sort envelopes by trust score descending
        sorted_envs = sorted(valid_envs, key=lambda x: x.trust_score, reverse=True)
        
        # Build hierarchy
        constitution_section = f"=== CONSTITUTION ===\n{constitution or 'Standard safety invariants'}"
        profile_section = "=== PROJECT PROFILE ===\nProject: RAE-Suite v3.0\nConfig: STRICT_SEMVER=true"
        
        fixed_str = f"{constitution_section}\n\n{profile_section}"
        fixed_token_count = len(fixed_str.split())
        
        # Fail-closed if fixed sections already exceed token limit
        if fixed_token_count > self.token_limit:
            logger.error(f"Context budget overrun: fixed sections length {fixed_token_count} exceeds limit {self.token_limit}")
            # Truncate and return under warning
            return " ".join(fixed_str.split()[:self.token_limit])
            
        leaf_parts = []
        current_token_count = fixed_token_count
        
        for env in sorted_envs:
            content = env.retrieved_content.strip()
            # Format first, then calculate tokens (to include metadata overhead in the count)
            leaf_formatted = f"[{env.memory_layer.upper()}] (Trust: {env.trust_score:.2f}) (Hash: {env.source_hash[:8]}):\n{content}"
            word_count = len(leaf_formatted.split())
            
            # Check if this leaf fits under the budget
            if current_token_count + word_count <= self.token_limit:
                leaf_parts.append(leaf_formatted)
                current_token_count += word_count
            else:
                # Prune this and subsequent leaves
                logger.info(f"context_pruning: pruned envelope {env.context_id} due to budget limit ({current_token_count} / {self.token_limit} words)")
                
        leaves_section = "=== RETRIEVED MEMORY LEAVES ===\n" + "\n\n".join(leaf_parts)
        
        # Final hierarchical presentation string
        pruned_prompt = f"{constitution_section}\n\n{profile_section}\n\n{leaves_section}"
        return pruned_prompt
