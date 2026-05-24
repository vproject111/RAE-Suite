import pytest
from unittest.mock import MagicMock, patch
from core.infra_reconciler import InfraReconciler

def test_infra_reconciler_tcp_verify_healthy():
    reconciler = InfraReconciler()
    
    # Mock socket connect to succeed
    with patch("socket.socket") as mock_socket:
        mock_conn = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_conn
        
        is_healthy = reconciler.verify_tcp_port("localhost", 8011)
        assert is_healthy is True


def test_infra_reconciler_tcp_verify_down():
    reconciler = InfraReconciler()
    
    # Mock socket connect to fail
    with patch("socket.socket") as mock_socket:
        mock_socket.return_value.__enter__.return_value.connect.side_effect = Exception("Connection refused")
        
        is_healthy = reconciler.verify_tcp_port("localhost", 9999)
        assert is_healthy is False


def test_infra_reconciler_service_outage_micro_restart_loop():
    reconciler = InfraReconciler()
    
    # Mock verify_tcp_port to always return False (port closed)
    reconciler.verify_tcp_port = MagicMock(return_value=False)
    
    service = "rae-quality"
    
    # 1. First failure -> trigger micro-restart 1/3
    res1 = reconciler.check_and_recover_service(service, "localhost", 8013)
    assert res1["status"] == "RESTARTED"
    assert res1["restarts"] == 1
    
    # 2. Second failure -> trigger micro-restart 2/3
    res2 = reconciler.check_and_recover_service(service, "localhost", 8013)
    assert res2["status"] == "RESTARTED"
    assert res2["restarts"] == 2
    
    # 3. Third failure -> trigger micro-restart 3/3
    res3 = reconciler.check_and_recover_service(service, "localhost", 8013)
    assert res3["status"] == "RESTARTED"
    assert res3["restarts"] == 3
    
    # 4. Fourth failure -> Hard stop! Escalate to human operator.
    res4 = reconciler.check_and_recover_service(service, "localhost", 8013)
    assert res4["status"] == "ESCALATED_TO_HUMAN"
    assert res4["restarts"] == 3
    assert "automated loop stopped" in res4["message"].lower()


def test_infra_reconciler_alembic_compatibility_passed():
    reconciler = InfraReconciler()
    safe_script = """
    def upgrade():
        op.create_table('audit_logs', sa.Column('id', sa.Integer()))
        op.add_column('memories', sa.Column('session_id', sa.String()))
    """
    is_compatible, reason = reconciler.verify_alembic_compatibility(safe_script)
    assert is_compatible is True
    assert "Passed" in reason


def test_infra_reconciler_alembic_compatibility_failed():
    reconciler = InfraReconciler()
    destructive_script = """
    def upgrade():
        op.drop_column('memories', 'strength')
    """
    is_compatible, reason = reconciler.verify_alembic_compatibility(destructive_script)
    assert is_compatible is False
    assert "destructive schema drift detected" in reason.lower()


def test_infra_reconciler_db_rollback_sla_success():
    reconciler = InfraReconciler()
    
    # Verify rollback to existing revision rev_initial
    success, duration = reconciler.auto_rollback_database("rev_initial")
    assert success is True
    assert duration < 15.0  # SLA limit: 15 seconds
    assert reconciler.db_state["current_revision"] == "rev_initial"


def test_infra_reconciler_db_rollback_missing_revision_failure():
    reconciler = InfraReconciler()
    
    success, duration = reconciler.auto_rollback_database("rev_nonexistent")
    assert success is False
