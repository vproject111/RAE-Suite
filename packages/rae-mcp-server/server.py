"""
RAE-Suite Unified MCP Server (Silicon Oracle v3.0).
Bridges Antigravity / Hermes Orchestrator with RAE Toolchain:
- rae_memory_search & rae_memory_store (Multi-layer agentic memory)
- rae_quality_audit (Deterministic sub-20ms AST inspector & SeniorityRanker)
- rae_phoenix_impact (SystemIndexer dependency & impact zone analysis)
- rae_sandbox_exec (Ephemeral Git Worktree + Docker --network none sandbox)
- rae_cluster_dispatch (Cluster Node 1-3 & OpenRouter Tier 1-3 task offloading)
"""

import os
import sys
import json
import time
import asyncio
import logging
from pathlib import Path
from typing import List

# Add paths to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
for p in [
    BASE_DIR / "packages" / "rae-agentic-memory" / "rae-core",
    BASE_DIR / "packages" / "rae-hive",
    BASE_DIR / "packages" / "rae-phoenix",
    BASE_DIR / "packages" / "rae-quality",
    BASE_DIR,
]:
    p_str = str(p)
    if p_str in sys.path:
        sys.path.remove(p_str)
    sys.path.insert(0, p_str)

import httpx  # noqa: E402
from mcp.server import Server  # noqa: E402
from mcp.server.stdio import stdio_server  # noqa: E402
from mcp.types import TextContent, Tool  # noqa: E402

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("RAE-MCP-Server")

from interceptor import PassiveMemoryInterceptor  # noqa: E402

# Imports of RAE engines
from engines.testing.ast_inspector import ASTInspector  # noqa: E402
from engines.governance.seniority_ranker import SeniorityRanker as QualitySeniorityRanker  # noqa: E402
from src.sandbox_manager import DockerSandboxManager, GitWorktreeManager  # noqa: E402
from core.layer_triad_runner import LayerTriadRunner  # noqa: E402

# Lazy indexer for Phoenix to ensure fast server boot
_system_indexer = None

def get_system_indexer():
    global _system_indexer
    if _system_indexer is None:
        from feniks.core.analysis.indexer import SystemIndexer
        project_root = os.getenv("RAE_PROJECT_ROOT", str(BASE_DIR))
        _system_indexer = SystemIndexer(project_root=project_root)
        _system_indexer.scan_project()
    return _system_indexer

# Initialize MCP Server
app = Server("rae-suite")
triad_runner = LayerTriadRunner()
sandbox_manager = DockerSandboxManager()
worktree_manager = GitWorktreeManager(repo_root=str(BASE_DIR))

RAE_API_URL = os.getenv("RAE_API_URL", "http://localhost:8000")
RAE_API_KEY = os.getenv("RAE_API_KEY", "dev-key")
RAE_TENANT_ID = os.getenv("RAE_TENANT_ID", "00000000-0000-0000-0000-000000000000")

HEADERS = {
    "X-API-Key": RAE_API_KEY,
    "X-Tenant-Id": RAE_TENANT_ID,
    "Content-Type": "application/json"
}

interceptor = PassiveMemoryInterceptor(
    api_url=RAE_API_URL,
    api_key=RAE_API_KEY,
    tenant_id=RAE_TENANT_ID,
)

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="rae_memory_search",
            description="Searches RAE agentic memory across working, episodic, semantic, and reflective layers with mathematical temporal decay and authority prioritization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query or concept"},
                    "layer": {"type": "string", "description": "Memory layer filter: 'all' or specific ('semantic', 'reflective', 'episodic', 'working')", "default": "all"},
                    "layers": {"type": "array", "items": {"type": "string"}, "description": "Optional list of memory layers"},
                    "project": {"type": "string", "description": "Project context filter (e.g. 'dreamsoft', 'screenwatcher', 'default')", "default": "default"},
                    "k": {"type": "integer", "description": "Number of top results to return", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="rae_memory_store",
            description="Stores a new insight, architectural rule, or event into RAE memory with ContextEnvelope provenance attribution and authority level tagging.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The information to persist"},
                    "layer": {"type": "string", "enum": ["working", "episodic", "semantic", "reflective"], "default": "semantic"},
                    "project": {"type": "string", "default": "default"},
                    "importance": {"type": "number", "description": "Importance score from 0.0 to 1.0", "default": 0.8},
                    "tags": {"type": "array", "items": {"type": "string"}, "default": []},
                    "metadata": {"type": "object", "default": {}},
                    "envelope": {
                        "type": "object",
                        "description": "ContextEnvelope provenance dictionary (source_type, project, attribution, authority_level: canonical|empirical|heuristic)",
                        "default": {}
                    }
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="rae_quality_audit",
            description="Performs deterministic AST code quality audit (McCabe Cyclomatic Complexity, Type Safety Ratio, antipattern detection, and Seniority Rank) in <20ms.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "The Python source code to inspect"},
                    "file_path": {"type": "string", "description": "Optional file path for contextual awareness", "default": "snippet.py"}
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="rae_phoenix_impact",
            description="Analyzes the project dependency graph to determine the impact zone (which files and symbols depend on a given file).",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to analyze (relative or absolute)"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="rae_phoenix_repair",
            description="Autonomously repairs, refactors, or transforms code using RAE-Phoenix language plugins (Python AST, TypeScript, PHP) and refactoring recipes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "The source code to repair or refactor"},
                    "file_path": {"type": "string", "description": "Path to the target file (determines language plugin)", "default": "snippet.py"},
                    "reason": {"type": "string", "description": "The repair objective or refactoring intention", "default": "Refactor and optimize code"},
                    "project": {"type": "string", "description": "Project name for contextual audit", "default": "default"}
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="rae_sandbox_exec",
            description="Executes a command safely inside an ephemeral Git Worktree mounted into an isolated Docker container (--network none) with automatic cleanup.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute"}
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="rae_sandbox_run",
            description="Alias for rae_sandbox_exec: executes a command safely inside an ephemeral Git Worktree mounted into an isolated Docker container (--network none).",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute"}
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="rae_cluster_dispatch",
            description="Offloads a coding, analysis, or review task to local GPU nodes (RTX 4080) or OpenRouter tier models.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The instruction or code for the model"},
                    "tier": {
                        "type": "string",
                        "enum": ["local_gpu_triad", "tier1_generate", "tier2_review_repair", "tier3_judge"],
                        "default": "tier1_generate",
                        "description": "Target tier: local_gpu_triad ($0.00 RTX 4080), tier1_generate ($0.05/1M Flash), tier2_review_repair ($0.66/1M), tier3_judge ($2.00/1M)"
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="rae_consolidate_traces",
            description="Consolidates passive working traces into episodic knowledge summaries using deterministic clustering.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "default": "default"},
                    "limit": {"type": "integer", "default": 50}
                }
            }
        )
    ]

async def _execute_tool(name: str, arguments: dict) -> List[TextContent]:
    try:
        if name == "rae_memory_search":
            query = arguments.get("query", "")
            layer_arg = arguments.get("layer", "all")
            layers = arguments.get("layers")
            if not layers:
                if layer_arg == "all":
                    layers = ["semantic", "reflective", "episodic", "working"]
                elif isinstance(layer_arg, list):
                    layers = layer_arg
                else:
                    layers = [str(layer_arg)]
            project = arguments.get("project", "default")
            k = arguments.get("k", 5)

            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    resp = await client.post(
                        f"{RAE_API_URL}/v2/memories/query",
                        headers=HEADERS,
                        json={"query": query, "layers": layers, "project": project, "k": k}
                    )
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        
                        # Authority-weighted prioritization: canonical > empirical > heuristic
                        def _authority_score(item):
                            meta = item.get("metadata", {}) or {}
                            auth = meta.get("authority_level") or meta.get("authority", "")
                            tags = item.get("tags", []) or []
                            if auth == "canonical" or "authority:canonical" in tags:
                                return 100.0
                            elif auth == "empirical" or "authority:empirical" in tags:
                                return 50.0
                            return 0.0

                        results.sort(key=lambda x: (_authority_score(x), x.get("score", 0.0)), reverse=True)
                        return [TextContent(type="text", text=json.dumps(results, indent=2, ensure_ascii=False))]
                    else:
                        return [TextContent(type="text", text=f"RAE Memory API returned status {resp.status_code}: {resp.text}")]
                except Exception as net_err:
                    return [TextContent(type="text", text=f"RAE Memory API offline ({net_err}). Search unavailable.")]

        elif name == "rae_memory_store":
            content = arguments.get("content", "")
            layer = arguments.get("layer", "semantic")
            project = arguments.get("project", "default")
            importance = arguments.get("importance", 0.8)
            tags = list(arguments.get("tags", []))
            metadata = dict(arguments.get("metadata", {}))
            envelope = arguments.get("envelope", {})

            if envelope:
                metadata["envelope"] = envelope
                if "authority_level" in envelope:
                    auth_tag = f"authority:{envelope['authority_level']}"
                    if auth_tag not in tags:
                        tags.append(auth_tag)
                    metadata["authority_level"] = envelope["authority_level"]
                if "source_type" in envelope and "source_type" not in metadata:
                    metadata["source_type"] = envelope["source_type"]

            payload = {
                "content": content,
                "layer": layer,
                "project": project,
                "importance": importance,
                "tags": tags,
                "metadata": metadata
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    resp = await client.post(f"{RAE_API_URL}/v2/memories/", headers=HEADERS, json=payload)
                    if resp.status_code in (200, 201):
                        return [TextContent(type="text", text=f"Successfully stored in RAE Memory ({layer} layer). ID: {resp.json().get('memory_id')}")]
                    else:
                        return [TextContent(type="text", text=f"Storage error ({resp.status_code}): {resp.text}")]
                except Exception as net_err:
                    return [TextContent(type="text", text=f"RAE Memory API offline ({net_err}).")]

        elif name == "rae_quality_audit":
            code = arguments.get("code", "")
            file_path = arguments.get("file_path", "snippet.py")

            # 1. Deterministic AST Analysis (<20ms)
            ast_res = ASTInspector.analyze_code(code, file_path=file_path)

            def _serialize_issue(issue):
                return issue.model_dump() if hasattr(issue, "model_dump") else issue.dict()

            if not ast_res["is_valid_syntax"]:
                return [TextContent(type="text", text=json.dumps({
                    "verdict": "REJECTED",
                    "seniority_level": "Junior Developer",
                    "score": 0.0,
                    "reasoning": f"SyntaxError: {ast_res.get('syntax_error')}",
                    "issues": [_serialize_issue(issue) for issue in ast_res["issues"]]
                }, indent=2))]

            complexity = ast_res["complexity"]
            type_safety = ast_res["type_safety"]
            coverage = 0.90  # Standard baseline

            score = QualitySeniorityRanker.calculate_score(coverage, complexity, type_safety)
            level = QualitySeniorityRanker.classify_level(score)
            verdict = "PASSED" if score >= 0.70 else "REJECTED"

            response_data = {
                "verdict": verdict,
                "seniority_level": level,
                "score": score,
                "ast_complexity": complexity,
                "max_function_complexity": ast_res["max_function_complexity"],
                "type_safety_ratio": f"{type_safety * 100:.1f}%",
                "typed_params": f"{ast_res['typed_params']}/{ast_res['total_params']}",
                "issues": [_serialize_issue(issue) for issue in ast_res["issues"]]
            }
            return [TextContent(type="text", text=json.dumps(response_data, indent=2))]

        elif name == "rae_phoenix_impact":
            file_path = arguments.get("file_path", "")
            indexer = get_system_indexer()
            impact = indexer.get_impact_zone(file_path)
            return [TextContent(type="text", text=json.dumps(impact, indent=2))]

        elif name == "rae_phoenix_repair":
            code = arguments.get("code", "")
            file_path = arguments.get("file_path", "snippet.py")
            reason = arguments.get("reason", "Refactor and optimize code")
            project = arguments.get("project", "default")

            # 1. Try delegating to live Phoenix HTTP service if running
            phoenix_url = os.getenv("RAE_PHOENIX_URL", "http://localhost:8012")
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.post(
                        f"{phoenix_url}/v2/phoenix/repair",
                        json={
                            "code": code,
                            "file_path": file_path,
                            "reason": reason,
                            "project": project,
                        },
                    )
                    if resp.status_code == 200:
                        return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]
            except Exception:
                pass

            # 2. In-process fallback via language plugins
            try:
                from feniks.core.plugins.base import RefactorIntention
                from feniks.core.plugins.manager import PluginManager

                pm = PluginManager()
                plugin = pm.get_plugin_for_file(file_path)
                if plugin:
                    intention = RefactorIntention(
                        objective=reason,
                        target_files=[file_path],
                        context={"project": project},
                    )
                    fixed_code = await plugin.execute_refactor(code, intention)
                    res = {
                        "status": "SUCCESS",
                        "plugin_used": plugin.name,
                        "file_path": file_path,
                        "refactored_code": fixed_code,
                        "objective": reason,
                    }
                    return [TextContent(type="text", text=json.dumps(res, indent=2))]
                else:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "status": "NO_PLUGIN",
                                    "message": f"No language plugin found for {file_path}. Supported: {pm.list_available_plugins()}",
                                },
                                indent=2,
                            ),
                        )
                    ]
            except Exception as e:
                return [TextContent(type="text", text=f"Phoenix repair error: {e}")]

        elif name in ("rae_sandbox_exec", "rae_sandbox_run"):
            command = arguments.get("command", "")
            worktree_path, branch_name = worktree_manager.create_worktree()
            try:
                res = sandbox_manager.run_in_sandbox(command, worktree_path)
                worktree_manager.prune_worktree(worktree_path, branch_name)
                return [TextContent(type="text", text=json.dumps(res, indent=2))]
            except Exception as e:
                worktree_manager.prune_worktree(worktree_path, branch_name)
                return [TextContent(type="text", text=f"Sandbox error: {e}")]

        elif name == "rae_cluster_dispatch":
            prompt = arguments.get("prompt", "")
            tier = arguments.get("tier", "tier1_generate")
            
            if tier == "cascade":
                res = await triad_runner.execute_3tier_cascade(task_text=prompt)
                return [TextContent(type="text", text=json.dumps(res, indent=2, ensure_ascii=False))]

            models = triad_runner.get_layer_models(tier)
            if not models:
                return [TextContent(type="text", text=f"No models configured for tier '{tier}'.")]

            # Dispatch asynchronously via triad runner
            res = await triad_runner.execute_layer_triad(layer_name=tier, payload_text=prompt)
            return [TextContent(type="text", text=json.dumps(res, indent=2, ensure_ascii=False))]

        elif name == "rae_consolidate_traces":
            project = arguments.get("project", "default")
            limit = arguments.get("limit", 50)
            res = await interceptor.consolidate_traces(project=project, limit=limit)
            return [TextContent(type="text", text=json.dumps(res, indent=2))]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Tool execution failed: {str(e)}")]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    start_time = time.perf_counter()
    try:
        res = await _execute_tool(name, arguments)
        duration_ms = (time.perf_counter() - start_time) * 1000
        await interceptor.capture_trace(
            tool_name=name,
            arguments=arguments,
            result=res,
            duration_ms=duration_ms,
        )
        return res
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        await interceptor.capture_trace(
            tool_name=name,
            arguments=arguments,
            result=None,
            duration_ms=duration_ms,
            error=e,
        )
        logger.error(f"Error handling tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Tool execution failed: {str(e)}")]

async def main():
    logger.info("Starting RAE-Suite Unified MCP Server (stdio transport)...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
