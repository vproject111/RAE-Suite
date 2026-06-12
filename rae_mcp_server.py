import asyncio
import json
import os
import subprocess
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

class RAESupervisor:
    def __init__(self):
        # Intelligent project/tenant detection is encapsulated in Foundation/Bridge
        self.enterprise_foundation = RAE_Enterprise_Foundation("rae-cloud-supervisor")
        self.bridge = self.enterprise_foundation.bridge
        self.api_url = self.bridge.api_url
        self.tenant_id = self.bridge.tenant_id

    @audited_operation("get_cloud_status")
    async def get_cloud_status(self):
        result = subprocess.check_output(
            ["docker", "ps", "--format", "json"], 
            stderr=subprocess.STDOUT
        ).decode()
        containers = [json.loads(line) for line in result.strip().split('\n') if line]
        return json.dumps(containers, indent=2)

    @audited_operation("run_diagnostic")
    async def run_diagnostic(self, script_name: str):
        script_path = os.path.join("scripts", script_name)
        if not os.path.exists(script_path):
            return f"Error: Script {script_name} not found."
        
        result = subprocess.check_output(
            ["python3", script_path], 
            stderr=subprocess.STDOUT
        ).decode()
        return result

    @audited_operation("search_rae_memory")
    async def search_rae_memory(self, query: str, project: str = None, layer: str = None, limit: int = 5):
        # We don't default project/layer here to allow RAE Engine to use its own context-aware defaults
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
        # We allow layer to be None so RAE Core can decide placement based on info_class/content
        payload = {
            "content": content,
            "project": project or self.bridge.project,
            "human_label": human_label,
            "layer": layer, # None allows RAE-Core choice
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
        result = subprocess.check_output(
            ["docker", "logs", "--tail", str(lines), service], 
            stderr=subprocess.STDOUT
        ).decode()
        return result

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
            description="Executes a diagnostic verification script.",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_name": {"type": "string"}
                },
                "required": ["script_name"],
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
            res = await supervisor.run_diagnostic(arguments["script_name"])
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
