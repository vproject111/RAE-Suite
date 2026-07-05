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
        sandbox_id = f"sbx-{task_id}-{uuid.uuid4().hex[:6]}"
        target_path = os.path.join(self.sandbox_root, sandbox_id)
        branch_name = f"agent/{sandbox_id}"

        logger.info("creating_worktree", task_id=task_id, path=target_path)

        try:
            # Check if branch exists, if not create it
            subprocess.run(
                ["git", "branch", branch_name, base_branch],
                cwd=self.repo_root,
                capture_output=True,
                check=False # Might already exist
            )

            # Create worktree
            subprocess.run(
                ["git", "worktree", "add", target_path, branch_name],
                cwd=self.repo_root,
                capture_output=True,
                check=True
            )
            return target_path
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode() if e.stderr else str(e)
            logger.critical(f"worktree_creation_failed: {err_msg}")
            raise RuntimeError(f"Fail-Closed Sandbox: Worktree creation failed: {err_msg}")

    def create_container(self, task_id: str, image_digest: str) -> str:
        """
        Creates a secure Docker container for task execution.
        Enforces digest verification, read-only rootfs, cap-drop, and no-new-privileges.
        """
        if "@sha256:" not in image_digest:
            raise ValueError("Security Violation: Docker image must be referenced by SHA-256 digest, not tag.")
            
        container_name = f"rae-sbx-{task_id}-{uuid.uuid4().hex[:6]}"
        logger.info("creating_secure_container", container=container_name, digest=image_digest)
        
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--read-only",
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
            logger.critical(f"container_creation_failed: {err_msg}")
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
