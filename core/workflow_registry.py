import logging
from typing import Dict, Optional, Any
from rae_contracts import WorkflowDefinition, WorkflowStep, RiskClass

logger = logging.getLogger(__name__)

class WorkflowRegistry:
    """
    Registry for managing and retrieving WorkflowDefinitions in RAE-Suite.
    """
    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._load_default_workflows()

    def register(self, workflow: WorkflowDefinition):
        self._workflows[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow: {workflow.workflow_id} (version: {workflow.version})")

    def get(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def _load_default_workflows(self):
        # Default safe-code-change workflow (Silicon Oracle v6.8 compliant)
        self.register(WorkflowDefinition(
            workflow_id="safe-code-change",
            name="Safe Code Change Workflow",
            version="1.0",
            entry_conditions={"allowed_risk_classes": ["R1", "R2", "R3"]},
            steps=[
                WorkflowStep(step_id="step1", capability="phoenix.plan_change", required_risk_class=RiskClass.R2),
                WorkflowStep(step_id="step2", capability="hive.prepare_worktree", required_risk_class=RiskClass.R1),
                WorkflowStep(step_id="step3", capability="phoenix.generate_patch", required_risk_class=RiskClass.R2),
                WorkflowStep(step_id="step4", capability="quality.evaluate_patch", required_risk_class=RiskClass.R1),
                WorkflowStep(step_id="step5", capability="hive.execute_tool", required_risk_class=RiskClass.R2)
            ],
            exit_conditions={"required_quality_status": "ACCEPT"},
            rollback_workflow_id="restore-snapshot"
        ))
        
        # Default rollback/recovery workflow
        self.register(WorkflowDefinition(
            workflow_id="restore-snapshot",
            name="Restore Snapshot Rollback Workflow",
            version="1.0",
            steps=[
                WorkflowStep(step_id="step1", capability="hive.execute_tool", required_risk_class=RiskClass.R2)
            ]
        ))
