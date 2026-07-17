import os
import shutil
import subprocess
import uuid
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SandboxManager:
    """
    Manages isolated execution environments (Git Worktrees & Secure Docker Containers) for RAE-Suite.
    Ensures that Risk > R1 operations are physically separated from the main codebase.
    """
    def __init__(self, repo_root: str, sandbox_root: Optional[str] = None):
        self.repo_root = os.path.abspath(repo_root)
        self.sandbox_root = sandbox_root or os.path.join(self.repo_root, "workspace", "sandboxes")
        os.makedirs(self.sandbox_root, exist_ok=True)

    def create_worktree(self, task_id: str, base_branch: str = "develop") -> str:
        """
        Creates a new Git Worktree for the given task.
        """
        safe_task_id = "".join([c for c in task_id if c.isalnum() or c in "-_"])
        sandbox_id = f"sbx-{safe_task_id}-{uuid.uuid4().hex}"
        target_path = os.path.abspath(os.path.join(self.sandbox_root, sandbox_id))
        
        # C6 Conformance: Prevent path traversal
        if not target_path.startswith(os.path.abspath(self.sandbox_root)):
            raise PermissionError("Fail-Closed Sandbox: Path traversal detected in sandbox creation.")
            
        branch_name = f"agent/{sandbox_id}"

        logger.info("creating_worktree", task_id=task_id, path=target_path)

        try:
            # Atomic worktree creation with new branch creation
            subprocess.run(
                ["git", "worktree", "add", "-b", branch_name, target_path, base_branch],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            return target_path
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip() if e.stderr else str(e)
            logger.critical(f"worktree_creation_failed: {err_msg}", extra={"stdout": e.stdout})
            raise RuntimeError(f"Fail-Closed Sandbox: Worktree creation failed: {err_msg}")

    def create_container(self, task_id: str, image_digest: str) -> str:
        """
        Creates a secure Docker container for task execution.
        Enforces digest verification, read-only rootfs, tmpfs, cap-drop, non-root user, and no-new-privileges.
        """
        if "@sha256:" not in image_digest:
            raise ValueError("Security Violation: Docker image must be referenced by SHA-256 digest, not tag.")
            
        safe_task_id = "".join([c for c in task_id if c.isalnum() or c in "-_"])
        container_name = f"rae-sbx-{safe_task_id}-{uuid.uuid4().hex}"
        logger.info("creating_secure_container", container=container_name, digest=image_digest)
        
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "--user", "1000:1000",
            "--network", "none",
            "--cap-drop=ALL",
            "--security-opt", "no-new-privileges:true",
            image_digest,
            "sleep", "3600"
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return container_name
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip() if e.stderr else str(e)
            logger.critical(f"container_creation_failed: {err_msg}", extra={"stdout": e.stdout})
            raise RuntimeError(f"Fail-Closed Sandbox: Docker container creation failed: {err_msg}")

    def cleanup_sandbox(self, sandbox_path: str):
        """
        Removes the worktree and the physical directory.
        """
        if not os.path.exists(sandbox_path):
            return

        logger.info("cleaning_up_sandbox", path=sandbox_path)
        
        try:
            # Remove worktree from git
            subprocess.run(
                ["git", "worktree", "remove", "--force", sandbox_path],
                cwd=self.repo_root,
                capture_output=True,
                check=False
            )
        except Exception:
            pass

        # Ensure directory is gone
        if os.path.exists(sandbox_path):
            shutil.rmtree(sandbox_path, ignore_errors=True)

    def list_active_sandboxes(self):
        """Lists currently allocated sandbox directories."""
        if not os.path.exists(self.sandbox_root):
            return []
        return os.listdir(self.sandbox_root)
