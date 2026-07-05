import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional
import httpx
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server.stdio import stdio_server

# Dynamic RAE-Core Path Discovery
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAE_CORE_PATH = os.environ.get("RAE_CORE_PATH")
if not RAE_CORE_PATH:
    potential_path = os.path.join(SCRIPT_DIR, "RAE-Suite/packages/rae-agentic-memory/rae-core")
    if os.path.exists(potential_path):
        RAE_CORE_PATH = potential_path

if RAE_CORE_PATH and RAE_CORE_PATH not in sys.path:
    sys.path.append(RAE_CORE_PATH)

from rae_core.utils.enterprise_guard import RAE_Enterprise_Foundation, audited_operation

from core.autonomy_kernel import AutonomyKernel
from rae_contracts import ExecutionStatus, QualityStatus

class RAESupervisor:
    def __init__(self):
        # Intelligent project/tenant detection is encapsulated in Foundation/Bridge
        self.enterprise_foundation = RAE_Enterprise_Foundation("rae-cloud-supervisor")
        self.bridge = self.enterprise_foundation.bridge
        self.api_url = self.bridge.api_url
        self.tenant_id = self.bridge.tenant_id
        # Instantiate Autonomy Kernel for security and capability gating
        self.kernel = AutonomyKernel(bridge=self.bridge, repo_root=".")

    @audited_operation("get_cloud_status")
    async def get_cloud_status(self):
        # Route through AutonomyKernel first
        receipt = await self.kernel.execute_task(
            goal_id="mcp-cloud-status-goal",
            task_id="mcp-status-task",
            intent="Fetch Docker container statuses via docker ps.",
            payload={"target_agent": "rae-hive", "command": "docker ps"}
        )
        if receipt.execution_status != ExecutionStatus.SUCCESS:
            return f"Error: Action blocked by Autonomy Kernel. Status: {receipt.execution_status}. State: {receipt.final_state}"

        # Enforce Tool Execution Gateway
        exit_code, stdout, stderr = self.kernel.tool_gateway.execute_tool(
            trace_id=receipt.trace_id,
            command=["docker", "ps", "--format", "json"],
            cwd=".",
            risk_class=receipt.risk_class
        )
        if exit_code != 0:
            return f"Error executing docker ps: {stderr}"

        containers = [json.loads(line) for line in stdout.strip().split('\n') if line]
        return json.dumps(containers, indent=2)

    @audited_operation("run_diagnostic")
    async def run_diagnostic(self, diagnostic_id: str):
        # Allowlist of registered diagnostic IDs (diagnostic_id)
        ALLOWED_DIAGNOSTICS = {
            "diag-001": {
                "script": "validate_rae_integration.py",
                "description": "Validation of RAE integration"
            },
            "diag-002": {
                "script": "test_cognitive_planning_integration.py",
                "description": "Validation of cognitive planning integration"
            }
        }

        if diagnostic_id not in ALLOWED_DIAGNOSTICS:
            return f"Error: Unauthorized or unknown diagnostic ID: {diagnostic_id}. Only registered diagnostic IDs are permitted."

        diag = ALLOWED_DIAGNOSTICS[diagnostic_id]
        script_name = diag["script"]
        script_path = os.path.join("scripts", script_name)
        if not os.path.exists(script_path):
            return f"Error: Script {script_name} not found."

        # Route through AutonomyKernel first
        intent = f"Execute diagnostic script {script_name} via ID {diagnostic_id}"
        receipt = await self.kernel.execute_task(
            goal_id="mcp-diagnostic-goal",
            task_id="mcp-diag-task",
            intent=intent,
            payload={"target_agent": "rae-quality", "script": script_name}
        )
        if receipt.execution_status != ExecutionStatus.SUCCESS:
            return f"Error: Action blocked by Autonomy Kernel. Status: {receipt.execution_status}. State: {receipt.final_state}"

        # Enforce Tool Execution Gateway
        exit_code, stdout, stderr = self.kernel.tool_gateway.execute_tool(
            trace_id=receipt.trace_id,
            command=["python3", script_path],
            cwd=".",
            risk_class=receipt.risk_class
        )
        if exit_code != 0:
            return f"Error executing diagnostic {diagnostic_id}: {stderr}"
        return stdout

    @audited_operation("search_rae_memory")
    async def search_rae_memory(self, query: str, project: str = None, layer: str = None, limit: int = 5):
        # Route through AutonomyKernel first
        intent = f"Search RAE memory query: {query}"
        receipt = await self.kernel.execute_task(
            goal_id="mcp-search-memory-goal",
            task_id="mcp-search-task",
            intent=intent,
            payload={"target_agent": "rae-hive", "query": query, "project": project, "layer": layer}
        )
        if receipt.execution_status != ExecutionStatus.SUCCESS:
            return f"Error: Action blocked by Autonomy Kernel. Status: {receipt.execution_status}. State: {receipt.final_state}"

        payload = {
            "query": query,
            "project": project or self.bridge.project,
            "k": limit
        }
        if layer:
            payload["layers"] = [layer]
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.api_url}/v2/memories/query",
                json=payload,
                headers={"X-Tenant-Id": self.tenant_id}
            )
            return json.dumps(resp.json(), indent=2)

    @audited_operation("create_rae_memory")
    async def create_rae_memory(self, content: str, human_label: str = None, project: str = None, layer: str = None, importance: float = 0.5, metadata: dict = {}, info_class: str = "internal"):
        # Route through AutonomyKernel first
        intent = f"Create RAE memory: {content[:30]}..."
        receipt = await self.kernel.execute_task(
            goal_id="mcp-create-memory-goal",
            task_id="mcp-create-task",
            intent=intent,
            payload={"target_agent": "rae-hive", "content": content, "info_class": info_class}
        )
        if receipt.execution_status != ExecutionStatus.SUCCESS:
            return f"Error: Action blocked by Autonomy Kernel. Status: {receipt.execution_status}. State: {receipt.final_state}"

        payload = {
            "content": content,
            "project": project or self.bridge.project,
            "human_label": human_label,
            "layer": layer,
            "importance": importance,
            "info_class": info_class,
            "metadata": metadata
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.api_url}/v2/memories/",
                json=payload,
                headers={"X-Tenant-Id": self.tenant_id}
            )
            if resp.status_code in [200, 201]:
                return f"✅ Memory successfully created via MCP!\nResponse: {resp.text}"
            else:
                return f"❌ Failed to create memory via MCP (Status {resp.status_code}): {resp.text}"

    @audited_operation("get_service_logs")
    async def get_service_logs(self, service: str, lines: int = 50):
        # Route through AutonomyKernel first
        intent = f"Retrieve recent logs for service container: {service}"
        receipt = await self.kernel.execute_task(
            goal_id="mcp-logs-goal",
            task_id="mcp-logs-task",
            intent=intent,
            payload={"target_agent": "rae-hive", "service": service, "lines": lines}
        )
        if receipt.execution_status != ExecutionStatus.SUCCESS:
            return f"Error: Action blocked by Autonomy Kernel. Status: {receipt.execution_status}. State: {receipt.final_state}"

        # Enforce Tool Execution Gateway
        exit_code, stdout, stderr = self.kernel.tool_gateway.execute_tool(
            trace_id=receipt.trace_id,
            command=["docker", "logs", "--tail", str(lines), service],
            cwd=".",
            risk_class=receipt.risk_class
        )
        if exit_code != 0:
            return f"Error retrieving logs for {service}: {stderr}"
        return stdout

supervisor = RAESupervisor()
server = Server("rae-cloud-supervisor")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="get_cloud_status",
            description="Returns the current status of all Docker containers.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="run_diagnostic",
            description="Executes a registered diagnostic verification script using its diagnostic_id.",
            inputSchema={
                "type": "object",
                "properties": {
                    "diagnostic_id": {"type": "string", "description": "Allowed IDs: diag-001, diag-002"}
                },
                "required": ["diagnostic_id"],
            },
        ),
        types.Tool(
            name="search_rae_memory",
            description="Searches the RAE Memory API.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "project": {"type": "string"},
                    "layer": {"type": "string"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="create_rae_memory",
            description="Creates and stores a new memory inside RAE. Leave 'layer' empty to let RAE decide placement.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "human_label": {"type": "string"},
                    "project": {"type": "string"},
                    "layer": {"type": "string"},
                    "info_class": {"type": "string", "enum": ["public", "internal", "confidential", "restricted"], "default": "internal"},
                    "importance": {"type": "number", "default": 0.5},
                    "metadata": {"type": "object"}
                },
                "required": ["content"],
            },
        ),
        types.Tool(
            name="get_service_logs",
            description="Retrieves recent logs for a specific service container.",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "lines": {"type": "integer", "default": 50}
                },
                "required": ["service"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.Content]:
    try:
        if name == "get_cloud_status":
            res = await supervisor.get_cloud_status()
        elif name == "run_diagnostic":
            res = await supervisor.run_diagnostic(arguments["diagnostic_id"])
        elif name == "search_rae_memory":
            res = await supervisor.search_rae_memory(**arguments)
        elif name == "create_rae_memory":
            res = await supervisor.create_rae_memory(**arguments)
        elif name == "get_service_logs":
            res = await supervisor.get_service_logs(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return [types.TextContent(type="text", text=res)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    # Enforce Network SSE Transport as default, stdio as fallback
    if os.environ.get("RAE_MCP_STDIO") != "1":
        import uvicorn
        from fastapi import FastAPI, Request
        from mcp.server.sse import SseServerTransport

        app = FastAPI(title="rae-cloud-supervisor")
        sse = SseServerTransport("/mcp/messages")

        @app.get("/mcp/sse")
        async def mcp_sse_endpoint(request: Request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="rae-cloud-supervisor",
                        server_version="2.1.0",
                        capabilities=server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )

        @app.post("/mcp/messages")
        async def mcp_messages_endpoint(request: Request):
            await sse.handle_post_message(request.scope, request.receive, request._send)

        @app.get("/health")
        def health():
            return {"status": "healthy"}

        port = int(os.environ.get("RAE_MCP_PORT", "8005"))
        print(f"Starting SSE MCP Server on port {port}")
        config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
        server_uvicorn = uvicorn.Server(config)
        await server_uvicorn.serve()
    else:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="rae-cloud-supervisor",
                    server_version="2.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

if __name__ == "__main__":
    asyncio.run(main())
