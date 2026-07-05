import pytest
from core.sandbox_manager import SandboxManager

def test_sandbox_docker_digest_verification():
    manager = SandboxManager(repo_root=".")
    
    # 1. Invalid image format (no digest) -> Should raise ValueError
    with pytest.raises(ValueError) as excinfo:
        manager.create_container("test-task", "python:3.12-alpine")
    assert "Security Violation: Docker image must be referenced by SHA-256 digest" in str(excinfo.value)
    
    # 2. Valid image format (with digest) but dummy hash -> Should raise RuntimeError (docker daemon fails to find it)
    with pytest.raises(RuntimeError) as excinfo:
        manager.create_container("test-task", "python@sha256:d8a72cf7540ffbac67e44215df5021db6e64ee00a9e78bc70000000000000000")
    assert "Fail-Closed Sandbox: Docker container creation failed" in str(excinfo.value)
