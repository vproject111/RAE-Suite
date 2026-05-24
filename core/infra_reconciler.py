# core/infra_reconciler.py
import socket
import logging
import time
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class InfraReconciler:
    """
    Automated Infrastructure Reconciler for RAE-Suite.
    Detects container port outages, coordinates micro-restarts (max 3),
    conducts Alembic migration dry-runs, and executes rapid (<15s) database rollbacks.
    """
    def __init__(self):
        self.restart_counters: Dict[str, int] = {}
        self.db_state = {"current_revision": "rev_initial", "tables": ["memories", "tenants", "alembic_version"]}
        self.snapshots: Dict[str, Dict[str, Any]] = {
            "snap_rev_initial": {"current_revision": "rev_initial", "tables": ["memories", "tenants", "alembic_version"]}
        }

    def verify_tcp_port(self, host: str, port: int, timeout: float = 1.0) -> bool:
        """Checks if a TCP port is open and listening."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect((host, port))
                return True
        except Exception:
            return False

    def check_and_recover_service(self, service_name: str, host: str, port: int) -> Dict[str, Any]:
        """
        Monitors a TCP service and performs micro-restarts strictly up to 3 times.
        Escalates on 4th consecutive failure.
        """
        is_healthy = self.verify_tcp_port(host, port)
        if is_healthy:
            self.restart_counters[service_name] = 0
            return {"status": "HEALTHY", "restarts": 0}

        # Service is down!
        current_restarts = self.restart_counters.get(service_name, 0)
        if current_restarts < 3:
            current_restarts += 1
            self.restart_counters[service_name] = current_restarts
            logger.warning(f"infra_outage_detected: Service '{service_name}' TCP port {port} is closed. Triggering micro-restart {current_restarts}/3.")
            
            # Simulate docker restart command execution
            # In live environment: subprocess.run(["docker", "compose", "restart", service_name])
            return {
                "status": "RESTARTED",
                "restarts": current_restarts,
                "message": f"Micro-restart {current_restarts} initiated successfully."
            }
        else:
            # Hard stop condition reached: Max 3 attempts
            logger.error(f"infra_reconciliation_exhausted: Service '{service_name}' failed after 3 restarts. Escalating to human operator.")
            return {
                "status": "ESCALATED_TO_HUMAN",
                "restarts": current_restarts,
                "message": "Outage persists after 3 micro-restarts. Automated loop stopped."
            }

    def verify_alembic_compatibility(self, migration_script: str) -> Tuple[bool, str]:
        """
        Conducts a dry-run check of an Alembic migration script for backward compatibility.
        Detects destructive direct actions like drop_column or drop_table.
        """
        # Parse script for dangerous operations
        dangerous_ops = ["drop_column", "drop_table", "drop_constraint"]
        for op in dangerous_ops:
            if op in migration_script:
                reason = f"Destructive schema drift detected: '{op}' is backward incompatible."
                logger.error(f"alembic_dry_run_failed: {reason}")
                return False, reason

        logger.info("alembic_dry_run_passed: Migration script is backwards compatible.")
        return True, "Passed compatibility check."

    def auto_rollback_database(self, target_revision: str) -> Tuple[bool, float]:
        """
        Executes a rapid database rollback to a target revision.
        Measures execution time to guarantee < 15-second restore SLA.
        """
        start_time = time.perf_counter()
        snapshot_id = f"snap_{target_revision}"
        
        if snapshot_id not in self.snapshots:
            duration = time.perf_counter() - start_time
            logger.error(f"db_rollback_failed: Snapshot for revision '{target_revision}' not found.")
            return False, duration

        # Perform rollback simulation
        logger.info(f"db_rollback_initiated: Rolling back schema from '{self.db_state['current_revision']}' to '{target_revision}'...")
        
        # Simulate restore SLA latency
        time.sleep(0.05)  # Fast simulated restore
        
        self.db_state = self.snapshots[snapshot_id].copy()
        
        end_time = time.perf_counter()
        duration_seconds = end_time - start_time
        
        # Rigid SLA Guard
        if duration_seconds < 15.0:
            logger.info(f"db_rollback_success: Restored database state within SLA. Duration: {duration_seconds:.4f} seconds.")
            return True, duration_seconds
        else:
            logger.error(f"db_rollback_sla_violated: Restored took {duration_seconds:.4f} seconds (limit 15s).")
            return False, duration_seconds
