"""Passive Memory Interceptor (Implicit Capture) for RAE-MCP-Server.

Transparently captures MCP tool execution traces as ContextEnvelope records
into the RAE 'working' memory layer without requiring explicit agent tool calls,
satisfying ISO 42001 & ISO 27001 auditability and continuous cognitive learning.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger("RAE-PassiveInterceptor")


class PassiveMemoryInterceptor:
    """Non-blocking, zero-overhead passive memory capture for MCP tool invocations."""

    SENSITIVE_KEYS = {
        "api_key",
        "apikey",
        "secret",
        "password",
        "token",
        "auth",
        "authorization",
        "credentials",
        "privkey",
    }

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        tenant_id: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout: float = 2.0,
    ):
        self.api_url = (api_url or os.getenv("RAE_API_URL", "http://localhost:8001")).rstrip("/")
        self.api_key = api_key or os.getenv("RAE_API_KEY", "dev-key")
        self.tenant_id = tenant_id or os.getenv("RAE_TENANT_ID", "00000000-0000-0000-0000-000000000000")

        if enabled is not None:
            self.enabled = enabled
        else:
            env_val = os.getenv("RAE_PASSIVE_INGESTION_ENABLED", "true").lower()
            self.enabled = env_val in ("1", "true", "yes", "on")

        self.timeout = timeout
        self.headers = {
            "X-API-Key": self.api_key,
            "X-Tenant-Id": self.tenant_id,
            "Content-Type": "application/json",
        }

    def sanitize_arguments(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive credentials or excessively long payloads from trace arguments."""
        sanitized = {}
        for k, v in args.items():
            k_lower = k.lower()
            if any(s in k_lower for s in self.SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, str) and len(v) > 500:
                sanitized[k] = v[:497] + "..."
            elif isinstance(v, (dict, list)):
                try:
                    s_repr = json.dumps(v)
                    if len(s_repr) > 500:
                        sanitized[k] = s_repr[:497] + "..."
                    else:
                        sanitized[k] = v
                except Exception:
                    sanitized[k] = str(v)[:200]
            else:
                sanitized[k] = v
        return sanitized

    def summarize_result(self, result: Any) -> str:
        """Create a compact summary string from tool results."""
        if result is None:
            return "None"
        if isinstance(result, list):
            # TextContent list from MCP
            texts = []
            for item in result:
                if hasattr(item, "text"):
                    texts.append(str(item.text))
                else:
                    texts.append(str(item))
            joined = "\n".join(texts)
            return joined[:500] + ("..." if len(joined) > 500 else "")
        if isinstance(result, (dict, list)):
            try:
                dumped = json.dumps(result, ensure_ascii=False)
                return dumped[:500] + ("..." if len(dumped) > 500 else "")
            except Exception:
                return str(result)[:500]
        return str(result)[:500]

    async def capture_trace(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        duration_ms: float,
        error: Optional[Exception] = None,
        fire_and_forget: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Record an execution trace into RAE's working layer.

        Args:
            tool_name: Name of the invoked tool.
            arguments: Input arguments dict.
            result: Execution result or TextContent list.
            duration_ms: Total execution duration in milliseconds.
            error: Exception if the tool execution raised.
            fire_and_forget: If True, schedules dispatch in background task.

        Returns:
            The constructed trace payload or None if skipped/disabled.
        """
        if not self.enabled:
            return None

        # Anti-recursion protection
        if tool_name in ("rae_memory_store",):
            return None

        status = "error" if error is not None else "success"
        sanitized_args = self.sanitize_arguments(arguments)
        res_summary = f"Error: {error}" if error is not None else self.summarize_result(result)
        project = str(arguments.get("project") or os.getenv("RAE_PROJECT", "default"))

        envelope = {
            "source_type": "mcp_tool_trace",
            "project": project,
            "attribution": {"tool_name": tool_name},
            "authority_level": "empirical",
            "status": status,
        }

        tags = [
            "mcp_trace",
            "implicit_capture",
            f"tool:{tool_name}",
            f"status:{status}",
        ]
        if error is not None:
            tags.append("error")

        content = (
            f"[MCP Trace] tool={tool_name} | status={status} | duration={duration_ms:.1f}ms\n"
            f"args={json.dumps(sanitized_args, ensure_ascii=False)}\n"
            f"result={res_summary}"
        )

        payload = {
            "content": content,
            "layer": "working",
            "project": project,
            "importance": 0.4,
            "tags": tags,
            "metadata": {
                "tool_name": tool_name,
                "status": status,
                "duration_ms": round(duration_ms, 2),
                "envelope": envelope,
                "implicit_capture": True,
            },
        }

        if fire_and_forget:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._send_payload(payload))
            except RuntimeError:
                # No running loop, send synchronously in executor or await
                await self._send_payload(payload)
        else:
            await self._send_payload(payload)

        return payload

    async def _send_payload(self, payload: Dict[str, Any]) -> bool:
        """Internal safe HTTP dispatcher."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.api_url}/v2/memories/",
                    headers=self.headers,
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    logger.debug("passive_trace_stored", tool=payload["metadata"]["tool_name"])
                    return True
                logger.warning(
                    "passive_trace_store_failed",
                    status_code=resp.status_code,
                    text=resp.text[:200],
                )
                return False
        except Exception as e:
            logger.debug("passive_trace_delivery_skipped", error=str(e))
            return False

    async def consolidate_traces(
        self, project: str = "default", limit: int = 50
    ) -> Dict[str, Any]:
        """Query working layer traces and consolidate recurring patterns into episodic layer."""
        if not self.enabled:
            return {"status": "disabled", "consolidated_count": 0}

        try:
            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                query_resp = await client.post(
                    f"{self.api_url}/v2/memories/query",
                    headers=self.headers,
                    json={
                        "query": "MCP Trace",
                        "layers": ["working"],
                        "project": project,
                        "k": limit,
                    },
                )
                if query_resp.status_code != 200:
                    return {"status": "query_failed", "consolidated_count": 0}

                results = query_resp.json().get("results", [])
                traces = [r for r in results if "mcp_trace" in r.get("tags", [])]

                if len(traces) < 2:
                    return {"status": "insufficient_traces", "consolidated_count": 0}

                # Cluster and create summary insight
                tool_counts: Dict[str, int] = {}
                for t in traces:
                    meta = t.get("metadata", {}) or {}
                    tool = meta.get("tool_name", "unknown")
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1

                summary_text = (
                    f"Consolidated Trace Summary for project '{project}':\n"
                    f"Total captured operations: {len(traces)}\n"
                    f"Tool frequency breakdown: {json.dumps(tool_counts)}"
                )

                store_resp = await client.post(
                    f"{self.api_url}/v2/memories/",
                    headers=self.headers,
                    json={
                        "content": summary_text,
                        "layer": "episodic",
                        "project": project,
                        "importance": 0.7,
                        "tags": ["consolidated_trace", "implicit_capture"],
                        "metadata": {
                            "trace_count": len(traces),
                            "tool_counts": tool_counts,
                            "authority_level": "empirical",
                        },
                    },
                )

                return {
                    "status": "success",
                    "consolidated_count": len(traces),
                    "memory_id": store_resp.json().get("memory_id") if store_resp.status_code in (200, 201) else None,
                }
        except Exception as e:
            logger.error("trace_consolidation_error", error=str(e))
            return {"status": "error", "error": str(e), "consolidated_count": 0}
