import pytest
from rae_contracts import RiskClass
from core.cognitive_planner import CognitivePlanner, CognitivePlan, PlannerBranch

@pytest.mark.asyncio
async def test_cognitive_planner_generation_and_mcts():
    planner = CognitivePlanner()
    intent = "Refactor the database adapter to support async batching"
    
    plan = await planner.plan_task(
        intent=intent,
        payload={},
        risk_class=RiskClass.R4
    )
    
    # Verify the plan matches specifications
    assert isinstance(plan, CognitivePlan)
    assert plan.intent == intent
    assert plan.risk_class == RiskClass.R4
    assert len(plan.branches) >= 3
    
    # Verify branches
    selected_count = 0
    for branch in plan.branches:
        assert isinstance(branch, PlannerBranch)
        assert branch.branch_id is not None
        assert branch.name in ["Async Batching Pipeline", "Thread-Pool Executor Wrapper", "Event-Driven Message Queue Broker"]
        assert 0.0 <= branch.viability_score <= 1.0
        assert len(branch.simulated_impacts) == 3  # step 1, 2, 3
        assert branch.critique_feedback != ""
        if branch.is_selected:
            selected_count += 1
            assert branch.branch_id == plan.selected_branch_id
            
    assert selected_count == 1
    assert plan.win_probability > 0.0
    assert plan.planning_duration_ms > 0.0

@pytest.mark.asyncio
async def test_cognitive_planner_general_fallback():
    planner = CognitivePlanner()
    intent = "Some completely unrelated request"
    
    plan = await planner.plan_task(
        intent=intent,
        payload={},
        risk_class=RiskClass.R2
    )
    
    assert isinstance(plan, CognitivePlan)
    assert len(plan.branches) >= 3
    # Check that fallback branch names are generated
    branch_names = [b.name for b in plan.branches]
    assert "Direct Inline Refactoring" in branch_names
    assert "Facade Pattern Isolation" in branch_names
    assert "Distributed Strategy Pattern" in branch_names
