import uuid
import math
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from rae_contracts import RiskClass, TaskState

logger = logging.getLogger(__name__)

class PlannerBranch(BaseModel):
    """
    Represents an architectural hypothesis/branch generated during planning.
    """
    branch_id: str = Field(default_factory=lambda: f"br-{uuid.uuid4().hex[:8]}")
    name: str
    description: str
    architectural_approach: str
    simulated_impacts: List[str] = Field(default_factory=list)
    viability_score: float = Field(0.0, description="Evaluated viability score (0.0 to 1.0)")
    critique_feedback: str = Field("", description="Feedback from the self-critique loop")
    is_selected: bool = False

class CognitivePlan(BaseModel):
    """
    The final cognitive plan containing all analyzed branches and the selected path.
    """
    plan_id: str = Field(default_factory=lambda: f"pln-{uuid.uuid4().hex[:8]}")
    intent: str
    risk_class: RiskClass
    branches: List[PlannerBranch] = Field(default_factory=list)
    selected_branch_id: Optional[str] = None
    win_probability: float = Field(0.0, description="Highest win probability selected path")
    planning_duration_ms: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ToTNode:
    """
    A node representing a state in the Monte Carlo Tree Search / Tree of Thoughts planning tree.
    """
    def __init__(self, name: str, state_type: str, description: str, parent: Optional["ToTNode"] = None):
        self.name = name
        self.state_type = state_type  # "root", "hypothesis", "action_step"
        self.description = description
        self.parent = parent
        self.children: List["ToTNode"] = []
        self.visits = 0
        self.value = 0.0  # Accumulated viability/critique score
        self.critique_feedback = ""

    @property
    def viability(self) -> float:
        if self.visits == 0:
            return 0.0
        return self.value / self.visits

    def add_child(self, name: str, state_type: str, description: str) -> "ToTNode":
        child = ToTNode(name, state_type, description, parent=self)
        self.children.append(child)
        return child

    def select_uct(self, exploration_constant: float = 1.414) -> "ToTNode":
        """
        Selects a child node using the Upper Confidence Bound applied to Trees (UCT).
        """
        if not self.children:
            return self

        best_score = -float("inf")
        best_child = self.children[0]

        for child in self.children:
            if child.visits == 0:
                # Prioritize unvisited nodes
                return child
            
            # UCT Formula: Exploitation + Exploration
            exploitation = child.value / child.visits
            exploration = exploration_constant * math.sqrt(math.log(self.visits) / child.visits)
            uct_score = exploitation + exploration

            if uct_score > best_score:
                best_score = uct_score
                best_child = child

        return best_child

class CognitivePlanner:
    """
    Cognitive Planner implementing Monte Carlo Tree Search (MCTS) and Tree of Thoughts (ToT).
    Generates distinct hypotheses, runs a Self-Critique loop against constitutional/codebase constraints,
    and returns the highest win-probability plan.
    """
    def __init__(self, constitution_path: Optional[str] = None):
        self.constitution_path = constitution_path
        self.codebase_constraints = [
            "Do no harm to production data",
            "Optimize for O(1) latency where possible",
            "Prefer explicit code over implicit magic",
            "Maintain absolute type safety (Pydantic)",
            "Strict Zero Warning Policy",
            "Relative project paths only (No hardcoded absolute paths)",
            "No dependencies on heavy libraries like sentence-transformers"
        ]

    def _generate_hypotheses(self, intent: str) -> List[Dict[str, str]]:
        """
        Generates 3 distinct architectural hypotheses for the intent.
        """
        intent_lower = intent.lower()

        # Branch template generator based on keywords
        if "database" in intent_lower or "db" in intent_lower or "refactor" in intent_lower:
            return [
                {
                    "name": "Async Batching Pipeline",
                    "description": "Implement async context managers and SQL-Alchemy async batch insertion.",
                    "approach": "Modifies the DB adapter to handle connection pooling via async pgpool and executes batch operations."
                },
                {
                    "name": "Thread-Pool Executor Wrapper",
                    "description": "Wrap existing synchronous batching inside a thread-pool executor.",
                    "approach": "Uses asyncio.to_thread to run synchronous database batch operations on separate background threads."
                },
                {
                    "name": "Event-Driven Message Queue Broker",
                    "description": "Offload batch writes to a memory queue (Redis/Celery) to make the write non-blocking.",
                    "approach": "Decouples the persistence layer by writing messages to Redis and processing them via Celery background tasks."
                }
            ]
        elif "tool" in intent_lower or "forge" in intent_lower:
            return [
                {
                    "name": "Native Python Parsing module",
                    "description": "Write a pure Python parser using standard libraries.",
                    "approach": "Uses struct and memoryview to read binary headers and parse them into structured dictionaries."
                },
                {
                    "name": "C-Extension wrapper",
                    "description": "Compile a lightweight C library wrapper using ctypes.",
                    "approach": "Compiles a small C parser library for fast parsing and links it using ctypes/cffi."
                },
                {
                    "name": "External subprocess daemon",
                    "description": "Call an external command line binary and capture stdout.",
                    "approach": "Spawns a subprocess shell running an existing compiler/utility tool and parses stdout JSON."
                }
            ]
        else:
            # General fallback hypotheses
            return [
                {
                    "name": "Direct Inline Refactoring",
                    "description": "Perform minimal contiguous changes to the target file.",
                    "approach": "Edits the code structure directly using inline async refactoring and small modifications."
                },
                {
                    "name": "Facade Pattern Isolation",
                    "description": "Introduce an abstraction layer/Facade interface.",
                    "approach": "Creates a new adapter or facade to isolate the complex changes behind a simplified, clean API."
                },
                {
                    "name": "Distributed Strategy Pattern",
                    "description": "Define polymorphic strategies and inject them dynamically.",
                    "approach": "Defines a clean Strategy abstract class and registers concrete implementation classes based on configuration."
                }
            ]

    def _evaluate_constraints(self, approach: str) -> List[Dict[str, Any]]:
        """
        Simulates how the approach fits codebase constraints.
        Returns a list of violations/compliance details.
        """
        critique_results = []
        approach_lower = approach.lower()

        # Constraint 1: Do no harm to production data
        if "drop" in approach_lower or "delete" in approach_lower:
            critique_results.append({
                "constraint": "Do no harm to production data",
                "status": "FAIL",
                "score_impact": -0.4,
                "reason": "Direct deletion/dropping identified in approach."
            })
        else:
            critique_results.append({
                "constraint": "Do no harm to production data",
                "status": "PASS",
                "score_impact": 0.1,
                "reason": "Safe from destructive production data operations."
            })

        # Constraint 2: Optimize for O(1) latency
        if "redis" in approach_lower or "pool" in approach_lower:
            critique_results.append({
                "constraint": "Optimize for O(1) latency where possible",
                "status": "PASS",
                "score_impact": 0.2,
                "reason": "Uses caching/pooling which significantly optimizes database latency."
            })
        elif "subprocess" in approach_lower or "thread" in approach_lower:
            critique_results.append({
                "constraint": "Optimize for O(1) latency where possible",
                "status": "WARN",
                "score_impact": -0.1,
                "reason": "Threading or process context-switching incurs latency overhead."
            })
        else:
            critique_results.append({
                "constraint": "Optimize for O(1) latency where possible",
                "status": "PASS",
                "score_impact": 0.0,
                "reason": "Standard baseline latency profile."
            })

        # Constraint 3: Prefer explicit code over implicit magic
        if "ctypes" in approach_lower or "dynamic" in approach_lower:
            critique_results.append({
                "constraint": "Prefer explicit code over implicit magic",
                "status": "FAIL",
                "score_impact": -0.2,
                "reason": "C-bindings or dynamic class loading relies on implicit runtime magic."
            })
        else:
            critique_results.append({
                "constraint": "Prefer explicit code over implicit magic",
                "status": "PASS",
                "score_impact": 0.1,
                "reason": "Uses explicit imports and structured OOP constructs."
            })

        # Constraint 4: Relative project paths only
        if "/" in approach_lower and not any(kw in approach_lower for kw in ["redis", "http", "postgres"]):
            if "absolute" in approach_lower or "home" in approach_lower:
                critique_results.append({
                    "constraint": "Relative project paths only",
                    "status": "FAIL",
                    "score_impact": -0.3,
                    "reason": "Likely utilizes absolute host filesystems."
                })
            else:
                critique_results.append({
                    "constraint": "Relative project paths only",
                    "status": "PASS",
                    "score_impact": 0.0,
                    "reason": "Paths are resolved relatively or dynamically."
                })
        else:
            critique_results.append({
                "constraint": "Relative project paths only",
                "status": "PASS",
                "score_impact": 0.1,
                "reason": "Does not introduce absolute directory path coupling."
            })

        return critique_results

    async def plan_task(self, intent: str, payload: Dict[str, Any], risk_class: RiskClass) -> CognitivePlan:
        """
        Main cognitive planning entry point. Runs the Monte Carlo Tree Search planner
        over 3 distinct hypotheses and returns the final CognitivePlan.
        """
        start_time = datetime.now(timezone.utc)
        logger.info("cognitive_planning_started", intent=intent, risk_class=risk_class)

        # 1. Initialize MCTS search tree root
        root = ToTNode(name="IntentRoot", state_type="root", description=intent)

        # 2. Expansion Phase: Generate at least 3 distinct architectural hypotheses
        hypotheses_data = self._generate_hypotheses(intent)
        for hyp in hypotheses_data:
            root.add_child(name=hyp["name"], state_type="hypothesis", description=f"{hyp['description']} Approach: {hyp['approach']}")

        # 3. Expansion Step: Generate Action steps under each hypothesis
        for child in root.children:
            child.add_child(name="Step 1: Setup Worktree", state_type="action_step", description="Create branch and isolated sandbox.")
            child.add_child(name="Step 2: Apply Patch", state_type="action_step", description=f"Implement: {child.description}")
            child.add_child(name="Step 3: Verification", state_type="action_step", description="Run coverage and compliance checks.")

        # 4. Simulation / Rollout & Critique Phase
        # Run 20 MCTS iterations to build statistics
        iterations = 20
        for _ in range(iterations):
            # Selection
            node = root
            while node.children:
                node = node.select_uct()

            # Rollout simulation & critique calculation
            base_viability = 0.5
            constraints_feedback = self._evaluate_constraints(node.description)
            score_delta = sum(item["score_impact"] for item in constraints_feedback)
            viability_score = max(0.0, min(1.0, base_viability + score_delta))

            # Format critique feedback details
            feedback_bullets = []
            for item in constraints_feedback:
                feedback_bullets.append(f"- [{item['status']}] {item['constraint']}: {item['reason']}")
            
            node.critique_feedback = "\n".join(feedback_bullets)

            # Backpropagation
            temp_node = node
            while temp_node is not None:
                temp_node.visits += 1
                temp_node.value += viability_score
                temp_node = temp_node.parent

        # 5. Compile PlannerBranches and select highest score
        branches = []
        best_branch = None
        highest_score = -1.0

        for child in root.children:
            viability = child.viability
            
            # Aggregate step feedback
            step_critiques = []
            for step in child.children:
                if step.critique_feedback:
                    step_critiques.append(step.critique_feedback)
            critique_str = f"Branch Critique:\n{child.critique_feedback or 'Pending'}\nSteps Critique:\n" + "\n".join(step_critiques)

            branch = PlannerBranch(
                name=child.name,
                description=child.description,
                architectural_approach=child.description,
                simulated_impacts=[step.name for step in child.children],
                viability_score=round(viability, 4),
                critique_feedback=critique_str
            )
            branches.append(branch)

            if viability > highest_score:
                highest_score = viability
                best_branch = branch

        if best_branch:
            best_branch.is_selected = True

        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000.0

        plan = CognitivePlan(
            intent=intent,
            risk_class=risk_class,
            branches=branches,
            selected_branch_id=best_branch.branch_id if best_branch else None,
            win_probability=round(highest_score, 4) if best_branch else 0.0,
            planning_duration_ms=round(duration_ms, 2)
        )

        logger.info(
            "cognitive_plan_finalized",
            plan_id=plan.plan_id,
            selected=best_branch.name if best_branch else "None",
            win_prob=plan.win_probability
        )
        return plan
