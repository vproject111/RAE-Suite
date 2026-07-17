import pytest
from core.context_broker import ContextBroker
from rae_contracts import ContextEnvelope
from datetime import datetime, timezone

def test_adaptive_retrieval_depth():
    broker = ContextBroker()
    
    # Case 1: Large gap between top two candidates -> depth should be small, reranking skipped
    candidates_standout = [
        {"id": "1", "score": 0.95},
        {"id": "2", "score": 0.70},
        {"id": "3", "score": 0.50}
    ]
    depth, rerank = broker.determine_retrieval_depth(candidates_standout)
    assert depth == 3
    assert not rerank
    
    # Case 2: Tiny gap (clustered/zbite scores) -> depth should be 30, reranking enabled
    candidates_clustered = [
        {"id": "1", "score": 0.88},
        {"id": "2", "score": 0.87},
        {"id": "3", "score": 0.85}
    ]
    depth, rerank = broker.determine_retrieval_depth(candidates_clustered)
    assert depth == 30
    assert rerank


def test_hierarchical_context_pruning():
    broker = ContextBroker(token_limit=45) # Small token limit to force pruning
    
    envelopes = [
        ContextEnvelope(
            context_id="ctx-1",
            source_uri="rae://mem/1",
            source_hash="sha-1",
            trust_score=0.9,
            information_class="internal",
            tenant_id="t-1",
            project_id="p-1",
            memory_layer="semantic",
            valid_until=datetime.now(timezone.utc),
            retrieved_content="This is high priority content that should fit in the context."
        ),
        ContextEnvelope(
            context_id="ctx-2",
            source_uri="rae://mem/2",
            source_hash="sha-2",
            trust_score=0.8,
            information_class="internal",
            tenant_id="t-1",
            project_id="p-1",
            memory_layer="reflective",
            valid_until=datetime.now(timezone.utc),
            retrieved_content="This is also important but might fit."
        ),
        ContextEnvelope(
            context_id="ctx-3",
            source_uri="rae://mem/3",
            source_hash="sha-3",
            trust_score=0.4,
            information_class="internal",
            tenant_id="t-1",
            project_id="p-1",
            memory_layer="working",
            valid_until=datetime.now(timezone.utc),
            retrieved_content="This is low priority garbage that should be pruned because it exceeds the small limit."
        )
    ]
    
    pruned_prompt = broker.prune_context(envelopes, constitution="Do no harm.")
    
    assert "CONSTITUTION" in pruned_prompt
    assert "PROJECT PROFILE" in pruned_prompt
    assert "high priority content" in pruned_prompt
    assert "also important but might fit" in pruned_prompt
    assert "low priority garbage" not in pruned_prompt # Pruned!
