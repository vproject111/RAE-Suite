import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from server import list_tools, call_tool

@pytest.mark.asyncio
async def test_list_tools():
    tools = await list_tools()
    tool_names = [t.name for t in tools]
    expected_tools = [
        "rae_memory_search",
        "rae_memory_store",
        "rae_quality_audit",
        "rae_phoenix_impact",
        "rae_sandbox_exec",
        "rae_sandbox_run",
        "rae_cluster_dispatch"
    ]
    for exp in expected_tools:
        assert exp in tool_names, f"Tool {exp} should be listed"

@pytest.mark.asyncio
async def test_quality_audit_valid_code():
    code = """def add_numbers(a: int, b: int) -> int:
    \"\"\"Sum two integers.\"\"\"
    return a + b
"""
    results = await call_tool("rae_quality_audit", {"code": code})
    assert len(results) == 1
    data = json.loads(results[0].text)
    assert data["verdict"] == "PASSED"
    assert data["seniority_level"] in ("Senior", "Advanced Senior")
    assert data["score"] >= 0.75
    assert data["typed_params"] == "3/3"

@pytest.mark.asyncio
async def test_quality_audit_syntax_error():
    code = "def invalid_syntax(:"
    results = await call_tool("rae_quality_audit", {"code": code})
    assert len(results) == 1
    data = json.loads(results[0].text)
    assert data["verdict"] == "REJECTED"
    assert data["seniority_level"] == "Junior Developer"
    assert data["score"] == 0.0

@pytest.mark.asyncio
async def test_phoenix_impact_tool():
    with patch("server.get_system_indexer") as mock_get_indexer:
        mock_indexer = MagicMock()
        mock_indexer.get_impact_zone.return_value = {
            "target": "packages/rae-quality/main.py",
            "dependents": ["packages/rae-phoenix/main.py"],
            "total_dependents": 1
        }
        mock_get_indexer.return_value = mock_indexer

        results = await call_tool("rae_phoenix_impact", {"file_path": "packages/rae-quality/main.py"})
        assert len(results) == 1
        data = json.loads(results[0].text)
        assert data["target"] == "packages/rae-quality/main.py"
        assert data["total_dependents"] == 1

@pytest.mark.asyncio
async def test_phoenix_repair_python_plugin():
    code = "def hello(): pass"
    results = await call_tool(
        "rae_phoenix_repair",
        {"code": code, "file_path": "test_module.py", "reason": "Refactor hello"}
    )
    assert len(results) == 1
    data = json.loads(results[0].text)
    assert data["status"] == "SUCCESS"
    assert data["plugin_used"] == "python"
    assert "test_module.py" in data["file_path"]

@pytest.mark.asyncio
async def test_memory_search_tool_with_authority_sorting():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"id": "mem-heuristic", "content": "Guess about architecture", "score": 0.98, "metadata": {"authority_level": "heuristic"}},
            {"id": "mem-canonical", "content": "Master Specification Rule", "score": 0.85, "metadata": {"authority_level": "canonical"}},
            {"id": "mem-empirical", "content": "Log output from test", "score": 0.90, "metadata": {"authority_level": "empirical"}}
        ]
    }
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
        results = await call_tool("rae_memory_search", {"query": "architecture", "layer": "all", "k": 3})
        assert len(results) == 1
        data = json.loads(results[0].text)
        assert len(data) == 3
        # Canonical must be sorted first due to authority boost!
        assert data[0]["id"] == "mem-canonical"
        assert data[1]["id"] == "mem-empirical"
        assert data[2]["id"] == "mem-heuristic"
        
        # Verify query payload passed all layers
        mock_post.assert_called_once()
        req_body = mock_post.call_args.kwargs["json"]
        assert "working" in req_body["layers"]
        assert "semantic" in req_body["layers"]

@pytest.mark.asyncio
async def test_memory_store_tool_with_envelope():
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"memory_id": "mem-uuid-123"}
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
        envelope = {
            "source_type": "architecture",
            "project": "dreamsoft",
            "authority_level": "canonical",
            "attribution": {"file_path": "docs/specs/CORE.md"}
        }
        results = await call_tool("rae_memory_store", {
            "content": "Rule: no mock values in production",
            "layer": "reflective",
            "project": "dreamsoft",
            "envelope": envelope
        })
        assert len(results) == 1
        assert "mem-uuid-123" in results[0].text
        
        # Verify envelope passed into request body
        req_body = mock_post.call_args.kwargs["json"]
        assert "authority:canonical" in req_body["tags"]
        assert req_body["metadata"]["envelope"] == envelope
        assert req_body["metadata"]["authority_level"] == "canonical"

@pytest.mark.asyncio
async def test_cluster_dispatch_tool():
    with patch("server.triad_runner.execute_layer_triad", new_callable=AsyncMock) as mock_triad:
        mock_triad.return_value = {
            "layer": "tier1_generate",
            "synthesis": "Code generated without issues",
            "reviews": []
        }
        results = await call_tool("rae_cluster_dispatch", {
            "prompt": "Create helper function",
            "tier": "tier1_generate"
        })
        assert len(results) == 1
        data = json.loads(results[0].text)
        assert data["layer"] == "tier1_generate"
        assert "Code generated" in data["synthesis"]

@pytest.mark.asyncio
async def test_sandbox_exec_and_run_tools():
    with patch("server.worktree_manager.create_worktree", return_value=("/tmp/wt", "agent/wt-123")), \
         patch("server.sandbox_manager.run_in_sandbox", return_value={"exit_code": 0, "output": "ok"}), \
         patch("server.worktree_manager.prune_worktree") as mock_prune:
        
        # Test rae_sandbox_exec
        res1 = await call_tool("rae_sandbox_exec", {"command": "echo hello"})
        assert len(res1) == 1
        data1 = json.loads(res1[0].text)
        assert data1["exit_code"] == 0
        
        # Test rae_sandbox_run alias
        res2 = await call_tool("rae_sandbox_run", {"command": "pytest"})
        assert len(res2) == 1
        data2 = json.loads(res2[0].text)
        assert data2["exit_code"] == 0
        assert mock_prune.call_count == 2
