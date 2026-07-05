#!/usr/bin/env python3
# scripts/validate_repo_manifest.py
import os
import sys
import json
import subprocess
import httpx
import asyncio

def run_command(args, cwd=None):
    try:
        res = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"error: {e.stderr.strip()}"

async def check_health(name, url):
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return name, True, "OK"
            return name, False, f"Status code: {resp.status_code}"
    except Exception as e:
        return name, False, str(e)

async def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(project_root, "REPOSITORY_MANIFEST.json")
    
    if not os.path.exists(manifest_path):
        print(f"❌ REPOSITORY_MANIFEST.json not found at: {manifest_path}")
        sys.exit(1)
        
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"❌ Failed to parse REPOSITORY_MANIFEST.json: {e}")
        sys.exit(1)
        
    print("🛡️  Validating REPOSITORY_MANIFEST.json...")
    
    errors = []
    
    # 1. Verify host commit SHA
    current_commit = run_command(["git", "rev-parse", "HEAD"], cwd=project_root)
    manifest_commit = manifest.get("host_commit_sha")
    if current_commit != manifest_commit:
        print(f"⚠️  Manifest commit SHA '{manifest_commit}' does not match current HEAD '{current_commit}'.")
        
    # 2. Verify submodules SHAs
    submodule_status = run_command(["git", "submodule", "status"], cwd=project_root)
    submodules_manifest = manifest.get("submodules", {})
    
    for sub_name, sub_info in submodules_manifest.items():
        sub_path = sub_info.get("path")
        expected_sha = sub_info.get("commit_sha")
        
        # Check physical directory
        full_sub_path = os.path.join(project_root, sub_path)
        if not os.path.exists(full_sub_path):
            errors.append(f"Submodule '{sub_name}' path does not exist: {sub_path}")
            continue
            
        # Get actual submodule SHA from git status
        actual_sha = "unknown"
        if submodule_status and not submodule_status.startswith("error"):
            for line in submodule_status.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == sub_path:
                    actual_sha = parts[0].strip("+-")
                    break
        
        if actual_sha == "unknown":
            # Fallback: run git in submodule directory
            actual_sha = run_command(["git", "rev-parse", "HEAD"], cwd=full_sub_path)
            
        if actual_sha != expected_sha:
            errors.append(f"Submodule '{sub_name}' SHA mismatch: expected {expected_sha}, got {actual_sha}")
        else:
            print(f"✅ Submodule '{sub_name}' is aligned at commit {expected_sha[:8]}")

    # 3. Ping health endpoints (warnings only, as they might be offline during build/CI)
    health_endpoints = manifest.get("health_endpoints", {})
    if health_endpoints:
        print("\n🔍 Checking health endpoints (optional)...")
        tasks = []
        for name, url in health_endpoints.items():
            tasks.append(check_health(name, url))
            
        results = await asyncio.gather(*tasks)
        for name, is_healthy, detail in results:
            if is_healthy:
                print(f"  [{name}] {url}: ✅ Online")
            else:
                print(f"  [{name}] {url}: ⚠️  Offline ({detail})")
                
    if errors:
        print("\n❌ MANIFEST VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
        
    print("\n✅ REPOSITORY_MANIFEST.json validation passed successfully!")
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
