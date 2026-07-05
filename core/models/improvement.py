import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class Hypothesis(BaseModel):
    hypothesis_id: str
    name: str
    description: str
    created_at: float = Field(default_factory=time.time)
    status: str = "draft"

class Experiment(BaseModel):
    experiment_id: str
    name: str
    hypothesis_id: str
    candidate: str
    success_criteria: str
    created_at: float = Field(default_factory=time.time)

class ExperimentRun(BaseModel):
    run_id: str
    experiment_id: str
    mode: str  # "shadow" | "canary"
    metrics: Dict[str, Any] = Field(default_factory=dict)
    result: str  # "pass" | "fail"
    trace_id: str
    created_at: float = Field(default_factory=time.time)

class ImprovementProposal(BaseModel):
    proposal_id: str
    experiment_id: str
    promotion_requirements: Dict[str, Any] = Field(default_factory=dict)

class PromotionDecision(BaseModel):
    proposal_id: str
    approved: bool
    reason: str

class RollbackDecision(BaseModel):
    proposal_id: str
    rollback_triggered: bool
    reason: str
