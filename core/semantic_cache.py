import time
import random
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SemanticCacheEntry(BaseModel):
    query: str
    response: str
    volatility_score: float  # High volatility = shorter TTL
    created_at: float = Field(default_factory=time.time)
    ttl: float
    embedding: List[float]

class ProbabilisticSemanticCache:
    """
    Implements the Probabilistic Cache Invalidation pattern.
    Limits caches to volatile semantic cache only, with absolutely no DB mutations.
    Enforces Semantic Neighborhood Eviction on mismatch detection.
    """
    def __init__(self, validation_probability: float = 0.05):
        self.cache: Dict[str, SemanticCacheEntry] = {}
        self.validation_probability = validation_probability

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude_v1 = sum(a * a for a in v1) ** 0.5
        magnitude_v2 = sum(b * b for b in v2) ** 0.5
        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0
        return dot_product / (magnitude_v1 * magnitude_v2)

    def get(self, query: str, query_embedding: List[float]) -> Optional[str]:
        """
        Retrieves matching cached result or None.
        Triggers probabilistic validation (p=0.05) and Semantic Neighborhood Eviction.
        """
        now = time.time()
        
        # 1. Exact or semantic lookup
        best_match_key = None
        best_match_entry = None
        best_sim = 0.0
        
        for k, entry in self.cache.items():
            # Check expiration
            if now > entry.created_at + entry.ttl:
                continue
                
            sim = self._cosine_similarity(query_embedding, entry.embedding)
            if sim > 0.95 and sim > best_sim:
                best_sim = sim
                best_match_key = k
                best_match_entry = entry

        if not best_match_entry:
            return None

        # 2. Probabilistic Invalidation Check
        if random.random() < self.validation_probability:
            logger.info(f"probabilistic_cache: Triggered random validation check (p={self.validation_probability}) for query: '{query}'")
            # Simulate validating with actual source (e.g. if the cached answer is still correct)
            # In our system, if it fails validation, we evict the neighborhood
            is_valid = self._mock_validate_source(query, best_match_entry.response)
            if not is_valid:
                logger.warning(f"probabilistic_cache: Validation mismatch detected! Evicting semantic neighborhood of '{query}'")
                self._evict_neighborhood(query_embedding)
                return None

        logger.info(f"probabilistic_cache: Cache hit (similarity={best_sim:.3f}) for query: '{query}'")
        return best_match_entry.response

    def set(self, query: str, response: str, volatility_score: float, embedding: List[float]):
        """
        Caches a response. TTL is dynamically scaled by 1 / volatility_score.
        """
        # Base TTL of 3600 seconds, scaled down by volatility
        ttl = max(60.0, 3600.0 / max(0.1, volatility_score))
        
        entry = SemanticCacheEntry(
            query=query,
            response=response,
            volatility_score=volatility_score,
            ttl=ttl,
            embedding=embedding
        )
        self.cache[query] = entry
        logger.info(f"probabilistic_cache: Cached query '{query}' (TTL={ttl:.1f}s, Volatility={volatility_score:.2f})")

    def _mock_validate_source(self, query: str, cached_response: str) -> bool:
        # In mock validation, say 90% chance it is valid, but fails if query contains "deprecated"
        if "deprecated" in query.lower():
            return False
        return True

    def _evict_neighborhood(self, target_embedding: List[float], threshold: float = 0.85):
        """
        Evicts all cached items with cosine similarity > threshold.
        """
        keys_to_evict = []
        for k, entry in self.cache.items():
            sim = self._cosine_similarity(target_embedding, entry.embedding)
            if sim > threshold:
                keys_to_evict.append(k)
                
        for k in keys_to_evict:
            del self.cache[k]
            logger.info(f"probabilistic_cache: Evicted semantic neighborhood key '{k}'")
