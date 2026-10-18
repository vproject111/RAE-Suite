"""Unit tests for PassiveMemoryInterceptor and Shadow Traces (Faza 4)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from interceptor import PassiveMemoryInterceptor
from server import call_tool, interceptor


@pytest.mark.asyncio
async def test_interceptor_sanitize_arguments():
    p = PassiveMemoryInterceptor(enabled=True)
    args = {
        "api_key": "secret_key_12345",
        "user_token": "bearer_abc",
        "safe_query": "search query here",
        "long_text": "x" * 600,
    }
    sanitized = p.sanitize_arguments(args)
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["user_token"] == "[REDACTED]"
    assert sanitized["safe_query"] == "search query here"
    assert len(sanitized["long_text"]) <= 500


@pytest.mark.asyncio
async def test_interceptor_skip_memory_store():
    p = PassiveMemoryInterceptor(enabled=True)
    res = await p.capture_trace(
        tool_name="rae_memory_store",
        arguments={"content": "new memory"},
        result="Success",
        duration_ms=10.5,
    )
    assert res is None


@pytest.mark.asyncio
async def test_interceptor_disabled():
    p = PassiveMemoryInterceptor(enabled=False)
    res = await p.capture_trace(
        tool_name="rae_quality_audit",
        arguments={"code": "pass"},
        result="Success",
        duration_ms=5.0,
    )
    assert res is None


@pytest.mark.asyncio
async def test_interceptor_capture_trace_payload():
    p = PassiveMemoryInterceptor(
        api_url="http://mock-rae:8001",
        api_key="mock-key",
        tenant_id="mock-tenant",
        enabled=True,
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"memory_id": "trace-uuid-1"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
        payload = await p.capture_trace(
            tool_name="rae_quality_audit",
            arguments={"code": "def foo(): pass", "project": "demo"},
            result="Passed",
            duration_ms=15.2,
            fire_and_forget=False,
        )

        assert payload is not None
        assert payload["layer"] == "working"
        assert payload["project"] == "demo"
        assert "implicit_capture" in payload["tags"]
        assert "tool:rae_quality_audit" in payload["tags"]
        assert payload["metadata"]["tool_name"] == "rae_quality_audit"
        assert payload["metadata"]["envelope"]["authority_level"] == "empirical"
        assert payload["metadata"]["envelope"]["source_type"] == "mcp_tool_trace"

        mock_post.assert_called_once()
        call_url = mock_post.call_args.args[0]
        assert call_url == "http://mock-rae:8001/v2/memories/"


@pytest.mark.asyncio
async def test_call_tool_passive_interception_integration():
    with patch.object(interceptor, "capture_trace", new_callable=AsyncMock) as mock_capture:
        code = 'def simple() -> int:\n    """Docstring."""\n    return 42\n'
        results = await call_tool("rae_quality_audit", {"code": code})
        assert len(results) == 1
        assert "PASSED" in results[0].text

        mock_capture.assert_called_once()
        kcall = mock_capture.call_args.kwargs
        assert kcall["tool_name"] == "rae_quality_audit"
        assert kcall["duration_ms"] >= 0.0
        assert kcall["result"] == results


@pytest.mark.asyncio
async def test_interceptor_consolidate_traces():
    p = PassiveMemoryInterceptor(api_url="http://mock-rae:8001", enabled=True)

    query_resp = MagicMock()
    query_resp.status_code = 200
    query_resp.json.return_value = {
        "results": [
            {
                "id": "t1",
                "tags": ["mcp_trace", "implicit_capture"],
                "metadata": {"tool_name": "rae_quality_audit"},
            },
            {
                "id": "t2",
                "tags": ["mcp_trace", "implicit_capture"],
                "metadata": {"tool_name": "rae_quality_audit"},
            },
        ]
    }

    store_resp = MagicMock()
    store_resp.status_code = 201
    store_resp.json.return_value = {"memory_id": "consolidated-uuid-99"}

    async def fake_post(url, **kwargs):
        if "query" in url:
            return query_resp
        return store_resp

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=fake_post):
        res = await p.consolidate_traces(project="test_proj")
        assert res["status"] == "success"
        assert res["consolidated_count"] == 2
        assert res["memory_id"] == "consolidated-uuid-99"


@pytest.mark.asyncio
async def test_interceptor_auto_consolidation_trigger():
    p = PassiveMemoryInterceptor(api_url="http://mock-rae:8000", enabled=True, auto_consolidate_interval=3)

    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"memory_id": "trace-1"}

    with patch.object(p, "consolidate_traces", new_callable=AsyncMock) as mock_consolidate, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):

        for i in range(2):
            await p.capture_trace(tool_name="tool_a", arguments={}, result="ok", duration_ms=1.0, fire_and_forget=False)
        assert mock_consolidate.call_count == 0

        # Third invocation should trigger auto-consolidation
        await p.capture_trace(tool_name="tool_a", arguments={}, result="ok", duration_ms=1.0, fire_and_forget=False)
        # Give asyncio loop a tick
        await asyncio.sleep(0.01)
        assert mock_consolidate.call_count == 1
