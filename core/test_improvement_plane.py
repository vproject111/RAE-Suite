import pytest
from core.improvement_plane import (
    ImprovementStore, HypothesisManager, ExperimentManager,
    ShadowRunner, CanaryManager, PromotionGate
)
from core.models.improvement import ImprovementProposal

class MockEvidenceRouter:
    def __init__(self):
        self.actions = []
    def record_action(self, action_record):
        self.actions.append(action_record)

class MockAuditorEngine:
    def __init__(self):
        self.allowed_proposals = set()
    def can_promote(self, proposal_id: str) -> bool:
        return proposal_id in self.allowed_proposals

def test_improvement_plane_full_cycle():
    # 1. Init store, managers, runners
    store = ImprovementStore()
    hyp_mgr = HypothesisManager(store)
    exp_mgr = ExperimentManager(store)
    
    evidence = MockEvidenceRouter()
    runner = ShadowRunner(store, evidence)
    
    canary = CanaryManager(error_rate_threshold=0.05)
    
    auditor = MockAuditorEngine()
    gate = PromotionGate(auditor, store)
    
    # 2. Create Hypothesis
    h = hyp_mgr.create_hypothesis("hyp-001", "Reduce Latency", "Use async cache lookup")
    assert h.status == "draft"
    
    # 3. Create Experiment
    e = exp_mgr.create_experiment("exp-001", "Async cache test", "hyp-001", "candidate_code_v1", "success_rate > 0.90")
    
    # 4. Run Shadow Run
    run = runner.run(e, {"simulated_latency": 35.0})
    assert run.result == "pass"
    assert len(evidence.actions) == 1
    assert evidence.actions[0].role == "shadow_runner"
    
    # 5. Verify Promotion Gate evaluates correctly
    proposal = ImprovementProposal(
        proposal_id="prop-001",
        experiment_id="exp-001",
        promotion_requirements={"rollback_plan": "Restore backup tag."}
    )
    
    # Promotion should be BLOCKED because Auditor hasn't approved it yet
    decision = gate.evaluate(proposal)
    assert not decision.approved
    assert "auditor_approved" in decision.reason
    
    # Approve in Auditor
    auditor.allowed_proposals.add("prop-001")
    
    # Now it should be APPROVED
    decision2 = gate.evaluate(proposal)
    assert decision2.approved
    
    # 6. Verify Canary Rollback
    rollback_ok = canary.evaluate_canary_health("exp-001", {"error_rate": 0.02})
    assert not rollback_ok.rollback_triggered
    
    rollback_fail = canary.evaluate_canary_health("exp-001", {"error_rate": 0.08})
    assert rollback_fail.rollback_triggered
