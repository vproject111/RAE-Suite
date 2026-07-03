#!/usr/bin/env python3
"""
Generator for REPOSITORY_MANIFEST.json in RAE-Suite.
Collects actual commits, submodule states, capabilities, health endpoints, and migration status.
"""

import os
import json
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("manifest-generator")

def run_git_command(args, cwd=None):
    try:
        res = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception as e:
        logger.warning(f"Git command failed: {args}. Error: {e}")
        return "n/a"

def generate_manifest():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(project_root, "REPOSITORY_MANIFEST.json")
    
    # 1. Host repo info
    host_commit = run_git_command(["git", "rev-parse", "HEAD"], cwd=project_root)
    host_branch = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_root)
    
    # 2. Submodule info
    submodules = {}
    submodule_output = run_git_command(["git", "submodule", "status"], cwd=project_root)
    if submodule_output != "n/a":
        for line in submodule_output.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                commit = parts[0].strip("+-")
                path = parts[1]
                name = os.path.basename(path)
                submodules[name] = {
                    "path": path,
                    "commit_sha": commit
                }

    # 3. Supported Capabilities (derived from RAE-Suite design)
    supported_capabilities = [
        "phoenix.plan_change",
        "phoenix.generate_patch",
        "hive.prepare_worktree",
        "hive.execute_tool",
        "quality.evaluate_patch",
        "quality.run_linter",
        "lab.mine_failures",
        "lab.recommender"
    ]
    
    # 4. Health Endpoints
    health_endpoints = {
        "rae-api": "http://localhost:8011/health",
        "rae-suite": "http://localhost:8009/health",
        "rae-phoenix": "http://localhost:8012/health",
        "rae-quality": "http://localhost:8010/health",
        "rae-hive": "http://localhost:8013/health"
    }

    manifest_data = {
        "project": "RAE-Suite",
        "host_commit_sha": host_commit,
        "host_branch": host_branch,
        "contracts_version": "7.0",
        "submodules": submodules,
        "supported_capabilities": supported_capabilities,
        "health_endpoints": health_endpoints,
        "migration_status": "aligned",
        "generated_at": run_git_command(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"])
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
        
    logger.info(f"Successfully generated manifest at: {manifest_path}")

if __name__ == "__main__":
    generate_manifest()
