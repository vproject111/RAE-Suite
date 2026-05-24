import os
import shutil
import tempfile
import subprocess
import hashlib
import json
import pytest
from core.gitops_daemon import GitOpsDaemon

@pytest.fixture
def temp_git_repo():
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
        
        # Set dummy git config for the repository
        subprocess.run(["git", "config", "user.email", "agent@rae-suite.local"], cwd=temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "RAE Agent"], cwd=temp_dir, capture_output=True, check=True)
        
        # Create a dummy initial commit so we have a HEAD and can branch from it
        dummy_file = os.path.join(temp_dir, "initial.txt")
        with open(dummy_file, "w") as f:
            f.write("initial content")
        subprocess.run(["git", "add", "initial.txt"], cwd=temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, capture_output=True, check=True)
    except Exception as e:
        shutil.rmtree(temp_dir)
        pytest.fail(f"Failed to initialize temp git repo fixture: {e}")
        
    yield temp_dir
    
    # Cleanup temp directory
    shutil.rmtree(temp_dir)


def test_create_agent_branch(temp_git_repo):
    daemon = GitOpsDaemon(temp_git_repo)
    task_id = "test-123"
    expected_branch = f"agent/task-{task_id}"
    
    branch_name = daemon.create_agent_branch(task_id)
    assert branch_name == expected_branch
    
    # Check that git actually checked out the branch
    res = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True
    )
    current_branch = res.stdout.strip()
    assert current_branch == expected_branch


def test_commit_changes_with_signature(temp_git_repo):
    daemon = GitOpsDaemon(temp_git_repo)
    
    # Create a new file to modify
    test_filename = "app_feature.py"
    test_filepath = os.path.join(temp_git_repo, test_filename)
    file_content = b"print('Hello, Silicon Oracle Autonomy!')"
    with open(test_filepath, "wb") as f:
        f.write(file_content)
        
    trace_id = "tr_auto_8899"
    commit_msg = "feat: implement advanced self-tuning decider"
    
    commit_hash, signature = daemon.commit_changes_with_signature(
        files=[test_filename],
        trace_id=trace_id,
        commit_msg=commit_msg
    )
    
    # Verify signature generation
    sha = hashlib.sha256()
    sha.update(trace_id.encode("utf-8"))
    sha.update(file_content)
    expected_sig = sha.hexdigest()
    
    assert signature == expected_sig
    assert commit_hash is not None
    assert len(commit_hash) > 0
    
    # Verify that the commit log has the trace details
    res = subprocess.run(
        ["git", "log", "-1", "--pretty=%B"],
        cwd=temp_git_repo,
        capture_output=True,
        text=True,
        check=True
    )
    commit_log = res.stdout.strip()
    assert commit_msg in commit_log
    assert f"trace_id: {trace_id}" in commit_log
    assert f"trace_signature: {signature}" in commit_log
    assert "signed_by: rae-gitops-daemon" in commit_log


def test_generate_pull_request(temp_git_repo):
    daemon = GitOpsDaemon(temp_git_repo)
    
    source = "agent/task-test-123"
    evidence_hash = "sha256_mock_evidence_pack_99aa88bb77"
    evidence_uri = "s3://rae-evidence-ledger/2026/05/24/test-123.tar.gz"
    trace_id = "tr_auto_8899"
    trace_signature = "sig_mock_123456789"
    
    # Test strict branch policy routing (master -> develop)
    pr_id_master = daemon.generate_pull_request(
        source_branch=source,
        target_branch="master",
        evidence_pack_hash=evidence_hash,
        evidence_pack_uri=evidence_uri,
        trace_id=trace_id,
        trace_signature=trace_signature
    )
    
    pr_file_master = os.path.join(daemon.pr_dir, f"{pr_id_master}.json")
    assert os.path.exists(pr_file_master)
    
    with open(pr_file_master, "r") as f:
        pr_data = json.load(f)
        
    assert pr_data["pr_id"] == pr_id_master
    assert pr_data["source_branch"] == source
    assert pr_data["target_branch"] == "develop"  # overridden from master
    assert pr_data["trace_id"] == trace_id
    assert pr_data["commit_signature"] == trace_signature
    assert pr_data["evidence_pack_hash"] == evidence_hash
    assert pr_data["evidence_pack_uri"] == evidence_uri
    assert pr_data["iso_compliance"] == "ISO-42001"
    assert pr_data["status"] == "OPEN"
    
    # Test that normal branches (e.g. develop or feature/*) are not overridden
    pr_id_dev = daemon.generate_pull_request(
        source_branch=source,
        target_branch="develop",
        evidence_pack_hash=evidence_hash,
        evidence_pack_uri=evidence_uri,
        trace_id=trace_id,
        trace_signature=trace_signature
    )
    
    pr_file_dev = os.path.join(daemon.pr_dir, f"{pr_id_dev}.json")
    assert os.path.exists(pr_file_dev)
    
    with open(pr_file_dev, "r") as f:
        pr_data_dev = json.load(f)
    assert pr_data_dev["target_branch"] == "develop"
