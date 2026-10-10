"""
RAE-Suite Hardened Cache-Aside & Semantic Watchdog
Includes:
1. Singleflight (request coalescing to prevent thundering herd).
2. TTL Jitter (base_ttl * random(0.85, 1.15)).
3. Negative caching for deterministic rejections.
4. Semantic Watchdog (detects non-improving repair loops / semantic stagnation).
"""

import time
import random
import hashlib
import threading
from enum import Enum
from typing import Dict, Any, Optional, Callable, List, Tuple
from pydantic import BaseModel, Field


class CacheEntryKind(str, Enum):
    VALUE = "VALUE"
    NEGATIVE = "NEGATIVE"


class CacheEntry(BaseModel):
    kind: CacheEntryKind
    key: str
    value: Any
    fresh_until: float
    stale_until: float


import difflib


class SemanticWatchdog:
    """
    Detects semantic loops (e.g. Phoenix patch stagnation, Auditor/Builder echo loops, silent hangs).
    Conforms to HIVE-CIRCUIT-BREAKER.md specification v1.0.
    """
    def __init__(self, max_stagnant_cycles: int = 3, echo_similarity_threshold: float = 0.90):
        self.max_stagnant_cycles = max_stagnant_cycles
        self.echo_similarity_threshold = echo_similarity_threshold
        self._history: Dict[str, List[float]] = {}
        self._rejections: Dict[str, List[str]] = {}
        self._heartbeats: Dict[str, Tuple[float, str]] = {}
        self._lock = threading.Lock()

    def record_score_and_check_stagnation(self, loop_id: str, quality_score: float) -> tuple[bool, str]:
        """
        Records quality score. If quality score has not improved for max_stagnant_cycles,
        returns (True, "SEMANTIC_LOOP_DETECTED").
        """
        with self._lock:
            scores = self._history.setdefault(loop_id, [])
            scores.append(quality_score)

            if len(scores) >= self.max_stagnant_cycles:
                recent = scores[-self.max_stagnant_cycles:]
                # If max score in recent window hasn't improved over first score in window
                if max(recent) <= recent[0]:
                    return True, f"SEMANTIC_LOOP_DETECTED: Quality score stagnant at {quality_score:.2f} for {self.max_stagnant_cycles} cycles"

            return False, "OK"

    def record_rejection_and_check_echo(self, loop_id: str, reason: str) -> tuple[bool, str]:
        """
        Monitors rejection reasons. If a task is rejected >= max_stagnant_cycles times
        and semantic/textual similarity between recent rejection reasons >= echo_similarity_threshold,
        triggers BLOCKED_LOOP (Anti-Echo rule).
        """
        with self._lock:
            reasons = self._rejections.setdefault(loop_id, [])
            reasons.append(reason)

            if len(reasons) >= self.max_stagnant_cycles:
                recent = reasons[-self.max_stagnant_cycles:]
                # Calculate pairwise similarity between recent rejections
                sim = difflib.SequenceMatcher(None, recent[-2], recent[-1]).ratio()
                if sim >= self.echo_similarity_threshold:
                    return True, f"BLOCKED_LOOP: Echo loop detected (similarity {sim:.2f} >= {self.echo_similarity_threshold}) across {len(reasons)} attempts"

            return False, "OK"

    def record_heartbeat(self, agent_id: str, status_text: str = "") -> None:
        """Records agent heartbeat with timestamp and status."""
        with self._lock:
            self._heartbeats[agent_id] = (time.time(), status_text)

    def check_heartbeat(self, agent_id: str, max_idle_seconds: float = 120.0) -> tuple[bool, str]:
        """
        Checks whether an agent has gone silent.
        If heartbeat missing for > max_idle_seconds, returns (True, "HEARTBEAT_TIMEOUT").
        """
        with self._lock:
            if agent_id not in self._heartbeats:
                return True, f"HEARTBEAT_MISSING: Agent '{agent_id}' never sent a heartbeat"
            last_time, status = self._heartbeats[agent_id]
            elapsed = time.time() - last_time
            if elapsed > max_idle_seconds:
                return True, f"HEARTBEAT_TIMEOUT: Agent '{agent_id}' silent for {elapsed:.1f}s (> {max_idle_seconds}s)"
            return False, "OK"


class HardenedSemanticCache:
    """
    Cache-Aside implementation featuring Singleflight request coalescing,
    TTL Jitter, and Negative Caching.
    """
    def __init__(self, base_ttl_s: float = 60.0, jitter_ratio: float = 0.15):
        self.base_ttl_s = base_ttl_s
        self.jitter_ratio = jitter_ratio
        self._cache: Dict[str, CacheEntry] = {}
        self._singleflight_locks: Dict[str, threading.Lock()] = {}
        self._lock = threading.Lock()

    def _compute_jittered_ttl(self) -> float:
        min_mult = 1.0 - self.jitter_ratio
        max_mult = 1.0 + self.jitter_ratio
        return self.base_ttl_s * random.uniform(min_mult, max_mult)

    def get_or_compute(self, key: str, compute_fn: Callable[[], Any], is_negative: bool = False) -> Any:
        """
        Gets value from cache or computes it under Singleflight request coalescing lock.
        """
        now = time.time()

        with self._lock:
            entry = self._cache.get(key)
            if entry and entry.fresh_until > now:
                return entry.value

            # Get or create singleflight lock per key
            sf_lock = self._singleflight_locks.setdefault(key, threading.Lock())

        # Singleflight execution
        with sf_lock:
            # Re-check cache inside lock
            with self._lock:
                entry = self._cache.get(key)
                if entry and entry.fresh_until > now:
                    return entry.value

            # Compute value
            val = compute_fn()
            ttl = self._compute_jittered_ttl()

            with self._lock:
                self._cache[key] = CacheEntry(
                    kind=CacheEntryKind.NEGATIVE if is_negative else CacheEntryKind.VALUE,
                    key=key,
                    value=val,
                    fresh_until=now + ttl,
                    stale_until=now + (ttl * 2)
                )
                self._singleflight_locks.pop(key, None)

            return val


class SemanticCacheEntry(BaseModel):
    query: str
    response: str
    volatility_score: float
    ttl: float
    embedding: List[float]
    created_at: float = Field(default_factory=time.time)


class ProbabilisticSemanticCache:
    """
    Implements the Probabilistic Cache Invalidation pattern.
    Limits caches to volatile semantic cache only, with absolutely no DB mutations.
    Enforces Semantic Neighborhood Eviction on mismatch detection.
    """
    def __init__(self, validation_probability: float = 0.05, max_ttl: float = 86400.0):
        self.cache: Dict[str, SemanticCacheEntry] = {}
        self.validation_probability = validation_probability
        self.max_ttl = max_ttl
        self.lock = threading.RLock()

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude_v1 = sum(a * a for a in v1) ** 0.5
        magnitude_v2 = sum(b * b for b in v2) ** 0.5
        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0
        return dot_product / (magnitude_v1 * magnitude_v2)

    def _purge_expired(self, now: float):
        """Purges expired cache entries to prevent memory leaks."""
        expired_keys = [k for k, entry in self.cache.items() if now > entry.created_at + entry.ttl]
        for k in expired_keys:
            del self.cache[k]

    def get(self, query: str, query_embedding: List[float]) -> Optional[str]:
        """
        Retrieves matching cached result or None.
        Triggers probabilistic validation (p=0.05) and Semantic Neighborhood Eviction.
        """
        now = time.time()
        
        with self.lock:
            self._purge_expired(now)
            
            best_match_key = None
            best_match_entry = None
            best_sim = 0.0
            
            for k, entry in self.cache.items():
                sim = self._cosine_similarity(query_embedding, entry.embedding)
                if sim > 0.95 and sim > best_sim:
                    best_sim = sim
                    best_match_key = k
                    best_match_entry = entry

            if not best_match_entry:
                return None

            # Probabilistic Invalidation Check
            if random.random() < self.validation_probability:
                is_valid = self._mock_validate_source(query, best_match_entry.response)
                if not is_valid:
                    self._evict_neighborhood(query_embedding)
                    return None

            return best_match_entry.response

    def set(self, query: str, response: str, volatility_score: float, embedding: List[float]):
        now = time.time()
        calculated_ttl = max(60.0, 3600.0 / max(0.1, volatility_score))
        ttl = min(calculated_ttl, self.max_ttl)
        
        entry = SemanticCacheEntry(
            query=query,
            response=response,
            volatility_score=volatility_score,
            ttl=ttl,
            embedding=embedding,
            created_at=now
        )
        
        with self.lock:
            self._purge_expired(now)
            self.cache[query] = entry

    def _mock_validate_source(self, query: str, cached_response: str) -> bool:
        if "deprecated" in query.lower():
            return False
        return True

    def _evict_neighborhood(self, target_embedding: List[float], threshold: float = 0.85):
        with self.lock:
            keys_to_evict = []
            for k, entry in self.cache.items():
                sim = self._cosine_similarity(target_embedding, entry.embedding)
                if sim > threshold:
                    keys_to_evict.append(k)
                    
            for k in keys_to_evict:
                del self.cache[k]

