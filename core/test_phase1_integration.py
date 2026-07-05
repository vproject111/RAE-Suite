import pytest
from core.context_broker import ContextBroker
from core.batch_engine import BatchOptimizationEngine, BatchTask
from core.model_router import ModelRouter
from core.telemetry_monitor import EmbeddingDriftDetector
from rae_contracts import RiskClass

def test_phase1_full_integration():
    # 1. Initialize all Phase 1 components
    broker = ContextBroker()
    batch_engine = BatchOptimizationEngine()
    model_router = ModelRouter()
    drift_detector = EmbeddingDriftDetector()
    
    # 2. Add tasks and group them (Batch Optimization & Efekt Skali Wiedzy)
    task1 = BatchTask(module="rae-phoenix", target_file="main.py", action_type="refactor")
    task2 = BatchTask(module="rae-phoenix", target_file="main.py", action_type="test")
    batch_engine.add_task(task1)
    batch_engine.add_task(task2)
    
    batches = batch_engine.optimize_and_group()
    assert len(batches) == 1
    
    # 3. Determine routing for the batch
    # Suppose we are processing phoenix task (Risk R2)
    model_name = model_router.route_task(RiskClass.R2)
    assert model_name == "llama-3.1-8b"
    assert model_router.registry[model_name].is_local
    
    # 4. Check for embedding drift in RAG baseline vs incoming queries
    baseline = [[0.1, 0.2, 0.3], [0.11, 0.21, 0.31], [0.09, 0.19, 0.29]] * 10
    current = [[0.1, 0.2, 0.3], [0.11, 0.21, 0.31], [0.09, 0.19, 0.29]] * 10
    psi, ks, is_drift = drift_detector.check_drift(baseline, current)
    assert not is_drift
    assert psi < 0.25
    
    # 5. Dispatch batch and verify metrics
    tokens_saved, time_saved = batch_engine.dispatch_batch(batches[0])
    assert tokens_saved == 15000  # setup_cost * (2 - 1)
    
    report = batch_engine.get_savings_report()
    assert report["tokens_saved"] == 15000
    assert report["tasks_processed"] == 2
