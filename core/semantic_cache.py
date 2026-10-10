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
from typing import Dict, Any, Optional, Callable
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
