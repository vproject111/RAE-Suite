import os
import json
import uuid
import hashlib
import logging
import subprocess
import time
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from rae_contracts import RiskClass, ExecutionMode, RedactionStatus, ToolInvocationEvent

logger = logging.getLogger(__name__)

class ToolGateway:
    """
    Implements the Tool Execution Gateway pattern.
    Validates, intercept, and registers all tool/command executions.
    Supports Trajectory Replay logging and Empty Run Prevention caching.
    """
    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.abspath(workspace_root)
        self.log_dir = os.path.join(self.workspace_root, "workspace", "trajectory_logs")
        self.output_dir = os.path.join(self.workspace_root, "workspace", "tool_outputs")
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, "trajectory_replay.jsonl")
        
        # In-memory cache for Empty Run Prevention (context_hash -> cached_result)
        self.empty_run_cache: Dict[str, Dict[str, Any]] = {}
        self._load_empty_run_cache()

    def _load_empty_run_cache(self):
        """Loads previous empty runs from the trajectory JSONL file to warm up the cache."""
        if not os.path.exists(self.log_path):
            return
        try:
            with open(self.log_path, "r") as f:
                for line in f:
                    entry = json.loads(line)
                    # If it was marked as an empty run, cache it
                    if entry.get("is_empty_run") and "context_hash" in entry:
                        self.empty_run_cache[entry["context_hash"]] = entry["result"]
        except Exception as e:
            logger.warning(f"Failed to load empty run cache: {e}")

    def _save_trajectory_entry(self, entry: Dict[str, Any]):
        """Appends a new trajectory replay log entry in JSONL format."""
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to save trajectory entry: {e}")

    def execute_tool(
        self, 
        trace_id: str, 
        command: List[str], 
        cwd: str, 
        risk_class: RiskClass,
        context_str: str = "",
        step_id: int = 1,
        rng_seed: int = 42,
        is_analysis: bool = False
    ) -> Tuple[int, str, str]:
        """
        Executes a command inside the gateway.
        Implements Empty Run Prevention and Trajectory Replay registration.
        """
        cmd_str = " ".join(command)
        # Compute hashes
        context_hash = hashlib.sha256((context_str or cmd_str).encode('utf-8')).hexdigest()
        input_hash = hashlib.sha256(cmd_str.encode('utf-8')).hexdigest()
        cwd_hash = hashlib.sha256(cwd.encode('utf-8')).hexdigest()

        # 1. Empty Run Prevention
        if is_analysis and context_hash in self.empty_run_cache:
            logger.info(f"empty_run_prevented: context_hash={context_hash}")
            cached = self.empty_run_cache[context_hash]
            return cached["exit_code"], cached["stdout"], cached["stderr"]

        # 2. Block destructive commands (failsafe Policy check)
        cmd_lower = cmd_str.lower()
        if any(bad in cmd_lower for bad in ["rm -rf /", "drop table", "truncate table", "drop database"]):
            raise PermissionError("Tool Execution Gateway: Destructive command blocked by policy engine.")

        # 3. Execution
        start_time = time.time()
        try:
            proc = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300
            )
            exit_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired:
            exit_code = -1
            stdout = ""
            stderr = "Command execution timed out (300s limit)."
        except Exception as e:
            exit_code = -1
            stdout = ""
            stderr = f"Command execution failed: {e}"

        duration_ms = (time.time() - start_time) * 1000

        # Compute output hashes
        stdout_hash = hashlib.sha256(stdout.encode('utf-8')).hexdigest()
        stderr_hash = hashlib.sha256(stderr.encode('utf-8')).hexdigest()

        # Save raw outputs to output dir
        raw_out_filename = f"out_{trace_id}_{step_id}.txt"
        raw_out_path = os.path.join(self.output_dir, raw_out_filename)
        try:
            with open(raw_out_path, "w") as f:
                f.write(f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}")
            raw_output_uri = f"file://{raw_out_path}"
        except Exception:
            raw_output_uri = "n/a"

        # 4. Check if this was an empty run (e.g. linter with no errors, or analyser saying 'no change required')
        is_empty_run = False
        if is_analysis:
            # Analyze outputs to determine if "no changes/no violations/success" was returned
            stdout_lower = stdout.lower()
            if any(ok in stdout_lower for ok in ["no changes", "no violations", "0 errors", "passed", "everything clean"]):
                is_empty_run = True

        # Log to replay file
        replay_entry = {
            "trace_id": trace_id,
            "step_id": step_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "context_hash": context_hash,
            "tool_input_hash": input_hash,
            "tool_output_hash": stdout_hash,
            "raw_output_uri": raw_output_uri,
            "rng_seed": rng_seed,
            "exit_code": exit_code,
            "is_empty_run": is_empty_run,
            "result": {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr
            }
        }
        self._save_trajectory_entry(replay_entry)

        # Cache if empty run
        if is_empty_run:
            self.empty_run_cache[context_hash] = replay_entry["result"]

        return exit_code, stdout, stderr
