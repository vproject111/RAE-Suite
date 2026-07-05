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
    def __init__(self, token_limit: int = 1500):
        self.token_limit = token_limit

    def determine_retrieval_depth(self, candidates: List[Dict[str, Any]]) -> Tuple[int, bool]:
        """
        Implements Adaptive Retrieval Depth.
        Analyzes candidate score distributions.
        Returns: (k_depth, run_reranker)
        """
        if not candidates:
            return 3, False
            
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
        # Sort envelopes by trust score descending
        sorted_envs = sorted(envelopes, key=lambda x: x.trust_score, reverse=True)
        
        # Build hierarchy
        constitution_section = f"=== CONSTITUTION ===\n{constitution or 'Standard safety invariants'}"
        profile_section = "=== PROJECT PROFILE ===\nProject: RAE-Suite v3.0\nConfig: STRICT_SEMVER=true"
        
        # Compile leaf data
        leaf_parts = []
        current_token_count = len(constitution_section.split()) + len(profile_section.split())
        
        for env in sorted_envs:
            content = env.retrieved_content.strip()
            # Estimate word count
            word_count = len(content.split())
            
            # Check if this leaf fits under the budget
            if current_token_count + word_count <= self.token_limit:
                leaf_parts.append(
                    f"[{env.memory_layer.upper()}] (Trust: {env.trust_score:.2f}) (Hash: {env.source_hash[:8]}):\n{content}"
                )
                current_token_count += word_count
            else:
                # Prune this and subsequent leaves
                logger.info(f"context_pruning: pruned envelope {env.context_id} due to budget limit ({current_token_count} / {self.token_limit} words)")
                
        leaves_section = "=== RETRIEVED MEMORY LEAVES ===\n" + "\n\n".join(leaf_parts)
        
        # Final hierarchical presentation string
        pruned_prompt = f"{constitution_section}\n\n{profile_section}\n\n{leaves_section}"
        return pruned_prompt
