import logging
import time
import uuid
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class BatchTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"tsk-{uuid.uuid4().hex[:6]}")
    module: str
    target_file: str
    action_type: str  # e.g., "refactor", "test", "lint"
    complexity: float = 0.5
    token_cost: int = 2000
    created_at: float = Field(default_factory=time.time)

class Batch:
    batch_id: str = Field(default_factory=lambda: f"bat-{uuid.uuid4().hex[:6]}")
    module: str
    tasks: List[BatchTask] = []
    is_warm: bool = False
    setup_cost: int = 15000  # Setup token cost (pruning base, env config, etc.)

class BatchOptimizationEngine:
    """
    Implements the Batch Optimization Engine for Context Economy.
    Groups tasks to minimize Context Switch Cost (CSC) and maximize setup amortization.
    Enforces the Knowledge Scale Effect (Efekt Skali Wiedzy).
    """
    def __init__(self):
        self.pending_tasks: List[BatchTask] = []
        self.active_batches: Dict[str, Batch] = {}
        self.warm_agents: Dict[str, float] = {}  # module -> last_active_timestamp
        
        # Metrics for savings report
        self.total_switches_prevented = 0
        self.total_tokens_saved = 0
        self.total_tasks_processed = 0

    def add_task(self, task: BatchTask):
        self.pending_tasks.append(task)
        logger.info(f"batch_engine: Added task {task.task_id} for module {task.module}")

    def optimize_and_group(self) -> List[Batch]:
        """
        Groups pending tasks by similarity of their target module.
        Implements Similarity Check -> Preparation Cost Detection -> Task Merging.
        """
        if not self.pending_tasks:
            return []

        batches_dict: Dict[str, Batch] = {}
        
        # 1. Similarity Check & Task Merging (Group by target module)
        for task in self.pending_tasks:
            module = task.module
            if module not in batches_dict:
                b = Batch()
                b.batch_id = f"bat-{uuid.uuid4().hex[:6]}"
                b.module = module
                b.tasks = []
                b.is_warm = module in self.warm_agents and (time.time() - self.warm_agents[module] < 600)
                batches_dict[module] = b
            
            batches_dict[module].tasks.append(task)

        # 2. Efekt Skali Wiedzy (Knowledge Scale Effect)
        # Pull extra related pending tasks (e.g. sharing target files) into active groups
        for module, b in batches_dict.items():
            active_files = {t.target_file for t in b.tasks}
            # Search for other tasks in the backlog that touch the same files, even if in a sub-module
            extra_tasks = []
            for task in self.pending_tasks:
                if task not in b.tasks and task.target_file in active_files:
                    extra_tasks.append(task)
                    
            for t in extra_tasks:
                b.tasks.append(t)
                logger.info(f"batch_engine: Knowledge Scale Effect - Merged extra task {t.task_id} into batch {b.batch_id} (touches same file {t.target_file})")

        self.pending_tasks = []
        return list(batches_dict.values())

    def dispatch_batch(self, batch: Batch) -> Tuple[int, float]:
        """
        Simulates dispatching a batch of tasks.
        Computes Context Switch Cost (CSC) and tokens saved.
        Returns: (tokens_saved, duration_saved)
        """
        num_tasks = len(batch.tasks)
        if num_tasks == 0:
            return 0, 0.0

        # Amortize setup cost
        # Without batching: each task would require warm setup (setup_cost)
        # With batching: we pay setup_cost only once
        setup_runs = num_tasks if not batch.is_warm else num_tasks + 1
        tokens_saved = batch.setup_cost * (setup_runs - 1)
        
        # Mark agent as warm
        self.warm_agents[batch.module] = time.time()
        
        self.total_switches_prevented += (num_tasks - 1)
        self.total_tokens_saved += tokens_saved
        self.total_tasks_processed += num_tasks

        logger.info(f"batch_engine: Dispatched batch {batch.batch_id} containing {num_tasks} tasks. Tokens saved: {tokens_saved}")
        return tokens_saved, (num_tasks - 1) * 1.5  # Simulate time saved in seconds

    def get_savings_report(self) -> Dict[str, Any]:
        """Computes Outcome Metrics for the savings report."""
        amortization_rate = (self.total_tokens_saved / (self.total_tasks_processed * 15000)) if self.total_tasks_processed else 0.0
        return {
            "switches_prevented": self.total_switches_prevented,
            "tokens_saved": self.total_tokens_saved,
            "tasks_processed": self.total_tasks_processed,
            "amortization_rate": amortization_rate,
            "batch_gain": self.total_tokens_saved * 0.000015  # Cost conversion estimate
        }
