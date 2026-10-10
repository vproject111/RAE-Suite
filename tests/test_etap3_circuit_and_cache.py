import time
import pytest
from core.circuit_breaker import TransportCircuitBreaker, CircuitState
from core.semantic_cache import HardenedSemanticCache, SemanticWatchdog


def test_transport_circuit_breaker_transitions():
    """TransportCircuitBreaker must trip to OPEN after threshold failures and transition to HALF_OPEN after timeout."""
    cb = TransportCircuitBreaker(failure_threshold=2, recovery_timeout_s=0.2)

    # 1. Successful execution -> CLOSED
    ok1, res1, err1 = cb.execute(lambda: "success_1")
    assert ok1
    assert res1 == "success_1"
    assert cb.state == CircuitState.CLOSED

    # 2. Record 2 failures -> OPEN
    cb.execute(lambda: 1 / 0)
    cb.execute(lambda: 1 / 0)
    assert cb.state == CircuitState.OPEN

    # 3. Executions blocked while OPEN
    ok_blocked, _, err_blocked = cb.execute(lambda: "success_2")
    assert not ok_blocked
    assert "CIRCUIT_BREAKER_OPEN" in err_blocked

    # 4. Wait for recovery timeout -> HALF_OPEN -> Success restores CLOSED
    time.sleep(0.25)
    ok_rec, res_rec, _ = cb.execute(lambda: "recovered")
    assert ok_rec
    assert res_rec == "recovered"
    assert cb.state == CircuitState.CLOSED


def test_semantic_watchdog_stagnation_detection():
    """SemanticWatchdog must detect stagnant quality scores over 3 cycles."""
    watchdog = SemanticWatchdog(max_stagnant_cycles=3)

    # Cycle 1 -> OK
    loop_1, msg1 = watchdog.record_score_and_check_stagnation("loop_phoenix", 0.70)
    assert not loop_1

    # Cycle 2 -> OK
    loop_2, msg2 = watchdog.record_score_and_check_stagnation("loop_phoenix", 0.70)
    assert not loop_2

    # Cycle 3 -> Stagnant (0.70 <= 0.70) -> Loop detected!
    loop_3, msg3 = watchdog.record_score_and_check_stagnation("loop_phoenix", 0.70)
    assert loop_3
    assert "SEMANTIC_LOOP_DETECTED" in msg3


def test_hardened_semantic_cache_singleflight_and_jitter():
    """HardenedSemanticCache must coalesce requests via Singleflight and compute jittered TTL."""
    cache = HardenedSemanticCache(base_ttl_s=10.0, jitter_ratio=0.15)
    compute_count = 0

    def compute_expensive():
        nonlocal compute_count
        compute_count += 1
        return f"result_{compute_count}"

    # First call -> computes
    val1 = cache.get_or_compute("key_1", compute_expensive)
    assert val1 == "result_1"
    assert compute_count == 1

    # Second call -> returned from cache (compute_count stays 1)
    val2 = cache.get_or_compute("key_1", compute_expensive)
    assert val2 == "result_1"
    assert compute_count == 1


def test_semantic_watchdog_echo_loop_detection():
    """SemanticWatchdog must detect repeated identical rejections (echo loop) over 3 cycles."""
    watchdog = SemanticWatchdog(max_stagnant_cycles=3, echo_similarity_threshold=0.90)

    # Rejection 1
    loop_1, msg1 = watchdog.record_rejection_and_check_echo("task-101", "Missing type annotations on parameter x")
    assert not loop_1

    # Rejection 2
    loop_2, msg2 = watchdog.record_rejection_and_check_echo("task-101", "Missing type annotations on parameter x in calculate")
    assert not loop_2

    # Rejection 3 with >90% identical reason -> BLOCKED_LOOP
    loop_3, msg3 = watchdog.record_rejection_and_check_echo("task-101", "Missing type annotations on parameter x in calculate")
    assert loop_3
    assert "BLOCKED_LOOP" in msg3


def test_semantic_watchdog_heartbeat_timeout():
    """SemanticWatchdog must detect silent agents when heartbeat is missing or expired."""
    watchdog = SemanticWatchdog()

    # Agent never sent heartbeat
    timed_out, msg = watchdog.check_heartbeat("agent-silent", max_idle_seconds=1.0)
    assert timed_out
    assert "HEARTBEAT_MISSING" in msg

    # Agent sends heartbeat -> OK
    watchdog.record_heartbeat("agent-active", "Working on AST node")
    timed_out_active, msg_active = watchdog.check_heartbeat("agent-active", max_idle_seconds=1.0)
    assert not timed_out_active

    # Agent expires after threshold
    time.sleep(1.05)
    timed_out_exp, msg_exp = watchdog.check_heartbeat("agent-active", max_idle_seconds=1.0)
    assert timed_out_exp
    assert "HEARTBEAT_TIMEOUT" in msg_exp
