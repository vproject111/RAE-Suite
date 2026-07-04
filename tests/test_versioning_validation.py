import pytest
from unittest.mock import patch
from rae_core.governance.versioning import (
    GitFlowStrategy,
    GitHubFlowStrategy,
    PermissiveStrategy,
    VersioningValidator,
)

def test_git_flow_strategy():
    strategy = GitFlowStrategy()
    
    # Valid branches
    assert strategy.validate("develop")[0] is True
    assert strategy.validate("master")[0] is True
    assert strategy.validate("main")[0] is True
    assert strategy.validate("feature/login-fix")[0] is True
    assert strategy.validate("bugfix/issue-12")[0] is True
    assert strategy.validate("release/1.2.3")[0] is True
    assert strategy.validate("release/1.2.3-rc.1")[0] is True
    assert strategy.validate("hotfix/1.2.4")[0] is True
    assert strategy.validate("checkpoint/editor-stable")[0] is True
    assert strategy.validate("HEAD")[0] is True
    assert strategy.validate("HEAD (detached)")[0] is True

    # Invalid branch patterns
    is_valid, msg = strategy.validate("random-branch")
    assert is_valid is False
    assert "does not follow standard Git Flow prefixes" in msg
    
    is_valid, msg = strategy.validate("release/v1.2.3")
    assert is_valid is False
    assert "uses legacy 'v' prefix" in msg

    is_valid, msg = strategy.validate("release/1.2")
    assert is_valid is False
    assert "does not comply with SemVer 2.0.0" in msg

    is_valid, msg = strategy.validate("hotfix/1.2.a")
    assert is_valid is False
    assert "does not comply with SemVer 2.0.0" in msg


def test_github_flow_strategy():
    strategy = GitHubFlowStrategy()
    
    # Permissive for standard branches
    assert strategy.validate("develop")[0] is True
    assert strategy.validate("random-branch")[0] is True
    assert strategy.validate("feature/xyz")[0] is True
    
    # Strict for release/hotfix prefixes
    assert strategy.validate("release/1.2.3")[0] is True
    
    is_valid, msg = strategy.validate("release/v1.2.3")
    assert is_valid is False
    assert "uses legacy 'v' prefix" in msg
    
    is_valid, msg = strategy.validate("release/1.2")
    assert is_valid is False
    assert "does not comply with SemVer 2.0.0" in msg


def test_permissive_strategy():
    strategy = PermissiveStrategy()
    assert strategy.validate("develop")[0] is True
    assert strategy.validate("random-branch")[0] is True
    assert strategy.validate("release/v1.2")[0] is True


@patch("rae_core.governance.versioning.VersioningValidator._get_current_branch")
def test_validator_git_flow_strict_failure(mock_get_branch):
    # Strict mode, invalid branch name -> raises ValueError
    mock_get_branch.return_value = "release/v1.2"
    validator = VersioningValidator(
        project_path="/tmp", 
        module_name="test-module",
        config={"strategy": "git-flow", "strict": True}
    )
    
    with pytest.raises(ValueError) as excinfo:
        validator.validate()
    assert "RAE Contract Violation in module 'test-module'" in str(excinfo.value)


@patch("rae_core.governance.versioning.VersioningValidator._get_current_branch")
def test_validator_git_flow_permissive_warning(mock_get_branch):
    # Non-strict mode, invalid branch name -> returns False, logs warning
    mock_get_branch.return_value = "release/v1.2"
    validator = VersioningValidator(
        project_path="/tmp", 
        module_name="test-module",
        config={"strategy": "git-flow", "strict": False}
    )
    
    assert validator.validate() is False


@patch("rae_core.governance.versioning.VersioningValidator._get_current_branch")
def test_validator_success_path(mock_get_branch):
    # Valid branch name -> returns True
    mock_get_branch.return_value = "release/1.2.3"
    validator = VersioningValidator(
        project_path="/tmp", 
        module_name="test-module",
        config={"strategy": "git-flow", "strict": True}
    )
    
    assert validator.validate() is True
