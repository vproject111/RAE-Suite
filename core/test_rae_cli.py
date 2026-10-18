import subprocess
import os
import sys

def test_rae_cli_help():
    # Execute help command to make sure CLI arguments parse correctly
    result = subprocess.run(
        [sys.executable, "scripts/rae.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "inspect" in result.stdout
    assert "replay" in result.stdout
    assert "fork" in result.stdout


def test_rae_cli_inspect_empty():
    # If trajectory_replay.jsonl doesn't exist or is empty, inspect should display summary
    result = subprocess.run(
        [sys.executable, "scripts/rae.py", "inspect"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "=== RAE TRAJECTORY INSPECTOR ===" in result.stdout
