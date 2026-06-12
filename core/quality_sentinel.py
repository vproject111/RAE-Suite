import os
import yaml
import uuid
import logging
from typing import Dict, Any, List, Optional
from rae_contracts import QualityStatus, QualityGateResult

logger = logging.getLogger(__name__)

class QualitySentinel:
    """
    Multi-Tier Quality Gate for RAE-Suite.
    Upgraded to enforce Constitutional AI principles (Anthropic approach).
    """
    def __init__(self, integrity_guard):
        self.integrity_guard = integrity_guard
        self.constitution_path = os.path.join(os.path.dirname(__file__), "constitution.yaml")
        self.principles = []
        self._load_constitution()

    def _load_constitution(self):
        try:
            if os.path.exists(self.constitution_path):
                with open(self.constitution_path, "r") as f:
                    config = yaml.safe_load(f)
                    self.principles = config.get("principles", [])
        except Exception as e:
            logger.error(f"failed_to_load_constitution: {e}")

    async def evaluate_quality(
        self, 
        trace_id: str, 
        original_test_code: str, 
        modified_test_code: str,
        metrics: Dict[str, Any]
    ) -> QualityGateResult:
        """
        Conducts a full quality audit including Constitutional validation.
        """
        logger.info("quality_audit_started", trace_id=trace_id)
        
        # 1. Test Integrity Check (AST)
        integrity_passed, violations = self.integrity_guard.verify_integrity(original_test_code, modified_test_code)
        
        # 2. Coverage Drift Check
        cov_before = metrics.get("coverage_before", 0.0)
        cov_after = metrics.get("coverage_after", 0.0)
        coverage_regression = cov_after < cov_before
        
        # 3. Static Vulnerability Scan
        critical_vulns = metrics.get("critical_vulns", 0)
        
        # 4. Constitutional AI Critique Checks
        patch_code = metrics.get("patch_code", "")
        constitutional_violations = 0
        critique_details = []

        if patch_code:
            # Check C6: Relative project paths only (No hardcoded absolute paths)
            if any(path in patch_code for path in ["/home/", "/etc/", "/usr/local/bin/"]):
                constitutional_violations += 1
                critique_details.append("Violates C6: Found absolute filesystem path in code patch.")
                
            # Check C1: Do no harm to production data
            if any(sql in patch_code.upper() for sql in ["DROP TABLE", "TRUNCATE TABLE", "DROP DATABASE"]):
                constitutional_violations += 1
                critique_details.append("Violates C1: Destructive database query command found.")
                
            # Check C3: Prefer explicit code over implicit magic (No heavy libraries)
            if "sentence_transformers" in patch_code:
                constitutional_violations += 1
                critique_details.append("Violates C3: Prohibited import of sentence_transformers.")

        # Determine Final Status
        status = QualityStatus.ACCEPT
        if not integrity_passed:
            status = QualityStatus.QUARANTINE
            logger.error(f"quality_violation_test_integrity: {violations}")
        elif constitutional_violations > 0:
            status = QualityStatus.REJECT
            logger.warning(f"quality_violation_constitutional: {critique_details}")
        elif coverage_regression:
            status = QualityStatus.REJECT
            logger.warning(f"quality_violation_coverage_drift: before={cov_before}, after={cov_after}")
        elif critical_vulns > 0:
            status = QualityStatus.REJECT
            logger.error(f"quality_violation_vulnerabilities count={critical_vulns}")
        elif not metrics.get("tests_passed", False):
            status = QualityStatus.REJECT
            logger.warning("quality_violation_tests_failed")

        result = QualityGateResult(
            status=status,
            existing_tests_passed=metrics.get("tests_passed", False),
            coverage_before=cov_before,
            coverage_after=cov_after,
            critical_vulnerabilities=critical_vulns,
            test_integrity_passed=integrity_passed,
            mutation_score=metrics.get("mutation_score", 0.0),
            architecture_violations=constitutional_violations,
            report_uri=" | ".join(critique_details) if critique_details else None
        )
        
        logger.info("quality_audit_completed", trace_id=trace_id, status=status)
        return result
