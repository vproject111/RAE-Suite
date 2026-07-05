import pytest
from core.batch_engine import BatchOptimizationEngine, BatchTask

def test_batch_optimization_engine():
    engine = BatchOptimizationEngine()
    
    # Add tasks
    engine.add_task(BatchTask(module="rae-phoenix", target_file="main.py", action_type="refactor"))
    engine.add_task(BatchTask(module="rae-phoenix", target_file="utils.py", action_type="test"))
    engine.add_task(BatchTask(module="rae-quality", target_file="checker.py", action_type="lint"))
    # Add another task that touches main.py but belongs to a different metadata search path (simulating overlap)
    # The engine should merge it into the active batch for main.py under Knowledge Scale Effect
    engine.add_task(BatchTask(module="rae-lab", target_file="main.py", action_type="analyse"))
    
    batches = engine.optimize_and_group()
    
    # Should have 3 batches (phoenix, quality, lab) originally but merged via file overlaps
    assert len(batches) >= 2
    
    # Find the phoenix batch
    phoenix_batch = next(b for b in batches if b.module == "rae-phoenix")
    # Phoenix batch should contain the lab task due to Knowledge Scale Effect because it touches main.py
    assert len(phoenix_batch.tasks) == 3
    assert any(t.module == "rae-lab" for t in phoenix_batch.tasks)
    
    # Dispatch and check savings
    tokens_saved, duration_saved = engine.dispatch_batch(phoenix_batch)
    assert tokens_saved > 0
    
    report = engine.get_savings_report()
    assert report["tokens_saved"] == tokens_saved
    assert report["tasks_processed"] == 3
    assert report["amortization_rate"] > 0.0
