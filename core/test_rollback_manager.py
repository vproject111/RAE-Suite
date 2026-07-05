import pytest
from core.rollback_manager import RollbackSLAManager, RollbackPlan, IncidentScope

def test_rollback_sla_matrix():
    manager = RollbackSLAManager()
    
    # 1. Valid plan below container_restart limit (10s <= 15s)
    plan = RollbackPlan(plan_id="p-1", action_type="container_restart", sla_threshold_seconds=10.0)
    assert manager.verify_plan(plan, "R2")
    
    # 2. Invalid plan exceeding git_worktree_revert limit (40s > 30s)
    plan_invalid = RollbackPlan(plan_id="p-2", action_type="git_worktree_revert", sla_threshold_seconds=40.0)
    assert not manager.verify_plan(plan_invalid, "R2")


def test_high_risk_sandbox_verification():
    manager = RollbackSLAManager()
    
    # High risk (R4/R5) without sandbox verification -> should fail
    plan_unverified = RollbackPlan(plan_id="p-3", action_type="container_restart", sla_threshold_seconds=12.0, verified_in_sandbox=False)
    assert not manager.verify_plan(plan_unverified, "R4")
    assert not manager.verify_plan(plan_unverified, "R5")
    
    # High risk (R4/R5) with sandbox verification -> should pass
    plan_verified = RollbackPlan(plan_id="p-4", action_type="container_restart", sla_threshold_seconds=12.0, verified_in_sandbox=True)
    assert manager.verify_plan(plan_verified, "R4")


def test_incident_quarantine_scopes():
    manager = RollbackSLAManager()
    
    # LOCAL scope quarantines only the specific context
    local_quarantine = manager.quarantine_incident("ctx-1", IncidentScope.LOCAL)
    assert local_quarantine == ["ctx-1"]
    
    # SERVICE_GROUP scope quarantines the context group
    group_quarantine = manager.quarantine_incident("ctx-2", IncidentScope.SERVICE_GROUP)
    assert "ctx-2" in group_quarantine
    assert len(group_quarantine) > 1
    
    # GLOBAL scope quarantines everything
    global_quarantine = manager.quarantine_incident("ctx-3", IncidentScope.GLOBAL)
    assert "all_active_contexts" in global_quarantine
