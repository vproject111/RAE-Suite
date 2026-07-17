import logging
import asyncio
from typing import List, Dict, Any, Tuple
from core.tool_gateway import ToolGateway
from rae_contracts import RiskClass

logger = logging.getLogger(__name__)

class SpeculativeToolExecutor:
    """
    Implements the Speculative Tool Execution pattern.
    Executes idempotent/read-only tools in parallel before final model commitment.
    Strictly limits speculative execution count to k=3.
    """
    def __init__(self, tool_gateway: ToolGateway):
        self.gateway = tool_gateway

    def _is_command_safe(self, command: List[str]) -> bool:
        """
        Only allows idempotent or read-only commands for speculative execution.
        Prevents injection by ensuring arguments do not contain shell metacharacters.
        """
        if not command:
            return False
            
        # Prevent shell metacharacters in any argument
        illegal_chars = [";", "&&", "||", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
        for arg in command:
            if any(char in arg for char in illegal_chars):
                logger.warning(f"speculative_executor: Blocked command containing forbidden characters: {command}")
                return False
                
        cmd_name = command[0].lower()
        # Allowlist of safe, read-only utilities
        if cmd_name == "git":
            # Only allow specific safe subcommands without arbitrary flags
            allowed_git_args = {"status", "diff", "log", "branch", "show"}
            return len(command) > 1 and command[1] in allowed_git_args
        elif cmd_name == "docker":
            # Only allow specific safe subcommands
            allowed_docker_args = {"ps", "logs", "images", "stats"}
            return len(command) > 1 and command[1] in allowed_docker_args
        elif cmd_name == "python3":
            # Only allow specific diagnostic scripts
            allowed_scripts = {
                "scripts/validate_git_flow.py",
                "scripts/validate_repo_manifest.py",
                "scripts/connect_cluster.py"
            }
            return len(command) > 1 and command[1] in allowed_scripts
            
        return False

    async def execute_speculatively(
        self, 
        trace_id: str, 
        commands: List[List[str]], 
        risk_class: RiskClass = RiskClass.R0
    ) -> Dict[str, Any]:
        """
        Executes up to k=3 safe commands in parallel.
        """
        # Limit to k=3
        safe_commands = [cmd for cmd in commands if self._is_command_safe(cmd)][:3]
        if not safe_commands:
            logger.info("speculative_executor: No safe commands matched for speculative run.")
            return {}

        logger.info(f"speculative_executor: Running {len(safe_commands)} speculative tools in parallel.")

        async def run_one(command: List[str]) -> Tuple[str, Dict[str, Any]]:
            # Run using the synchronous execute_tool within a threadpool or executor
            cmd_str = " ".join(command)
            loop = asyncio.get_running_loop()
            
            # Execute command inside ToolGateway
            exit_code, stdout, stderr = await loop.run_in_executor(
                None,
                self.gateway.execute_tool,
                trace_id,
                command,
                ".",
                risk_class
            )
            
            return cmd_str, {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr
            }

        # Run tasks in parallel
        tasks = [run_one(cmd) for cmd in safe_commands]
        results = await asyncio.gather(*tasks)
        
        return dict(results)
