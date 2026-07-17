# 🗺️ Hard Frames Rollout & Integration Plan: RAE-Suite v3.4+

This document outlines the step-by-step rollout of **Hard Frames Mode** across the RAE-Suite cluster. It ensures a zero-hallucination execution path by systematically wrapping all modules in code-level Autonomy Sequence contracts.

---

## ⚙️ Dual-Execution Modes (Tryby Uruchomienia)

The system supports two modes of execution, toggled dynamically via the `RAE_AUTONOMY_MODE` environment variable:

1. **Ordinary Mode (`RAE_AUTONOMY_MODE=ordinary`)**:
   - **Behavior**: The runtime tracks and journals the Sequence of Autonomy state transitions for auditing purposes, but does **not** block execution or throw exceptions when states are skipped or tools are called out of order.
   - **Usage**: Recommended for local development, rapid prototyping, and exploratory tasks.

2. **Hard Frames Mode (`RAE_AUTONOMY_MODE=hard`)**:
   - **Behavior**: Absolute enforcement of the Sequence of Autonomy. Any invalid transition (e.g. attempting actions before capability clearance) or security policy violation (e.g. restricted data leakage) throws a `ContractViolationError` and aborts immediately.
   - **Usage**: Mandatory for production, CI/CD pipelines, and high-concurrency environments.

---

## 📅 Rollout Phases

### 🏁 Phase 1: RAE-Core Hard Gating (Completed)
- **Objective**: Establish the core state machine, enforcer framework, and security boundaries.
- **Deliverables**:
  - `AutonomyState` Enum in `rae_core/models/contracts.py`.
  - `HardFrameEnforcer` transition engine in `rae_core/governance/frame_enforcer.py`.
  - Integration into `RAERuntime` processing loops in `rae_core/runtime.py`.
- **Status**: **100% Implemented & Verified** via unit tests (`test_hard_frames.py`).

---

### 📡 Phase 2: A2A Bridge State Propagation (Release `3.4.0-rc.1`)
- **Objective**: Propagate autonomy state metadata across modules during A2A routing.
- **Tasks**:
  1. Update `apps/memory_api/api/v2/bridge.py` to extract `autonomy_state` from incoming requests and inject it into the outgoing payload headers.
  2. Implement an validation interceptor in `rae-quality` and `rae-phoenix` that checks headers and blocks processing if the incoming state sequence is out of order.
  3. Propagate the signed `autonomy_journal` array in all A2A bridge responses.

---

### 🛡️ Phase 3: Sandbox & Dry-Run Enforcement (Release `3.5.0-rc.1`)
- **Objective**: Programmatically lock workspace write operations until sandbox setup is complete.
- **Tasks**:
  1. Bind filesystem execution tools (`write_file`, `replace_content`) to verify `enforcer.current_state == AutonomyState.SANDBOX_READY`.
  2. Implement dry-run tool mocks that run automatically in `AutonomyState.DRY_RUN_PASSED` phase before real changes are applied.
  3. Configure automatic git-worktree rollbacks triggered on `ROLLBACK_TRIGGERED` state transitions.

---

### ⚖️ Phase 4: Production Rollout & Auditing (Release `3.6.0`)
- **Objective**: Full cluster enforcement and cryptographic auditing.
- **Tasks**:
  1. Set default environment variable `RAE_AUTONOMY_MODE=hard` across all Compose service files.
  2. Store the cryptographically hashed `Evidence Pack` and signed `autonomy_journal` in the episodic database for auditing.
  3. Create real-time dashboard widgets visualizing active autonomy states and failed/escalated state transitions.
