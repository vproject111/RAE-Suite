from rae_core.models.behavior import BehaviorSignal, BehaviorViolation, DepartmentBehaviorContract
from typing import List
import logging

# New imports for Oracle Sentinel v1.3
from rae_contracts import MinimumAuditableEvent, ISOAuditRecord
from rae_auditor import ComplianceAuditor

logger = logging.getLogger(__name__)

class AuditorEngine:
    """
    Advanced behavioral analysis engine for RAE-Suite.
    Transforms raw agent signals into formal compliance violations.
    Integrated with Oracle Sentinel v1.3 compliance auditor layer.
    """
    
    def __init__(self):
        self.compliance_auditor = ComplianceAuditor()

    def collect_behavior_signals(self, observed_payloads: list) -> List[BehaviorSignal]:
        """Maps heterogeneous runtime observations into structured BehaviorSignals."""
        result = []
        for p in observed_payloads:
            try:
                result.append(BehaviorSignal(**p))
            except Exception as e:
                logger.error(f"Failed to map signal payload: {e}")
        return result

    def evaluate_behavioral_contract(self, contract: DepartmentBehaviorContract, signals: List[BehaviorSignal]) -> List[BehaviorViolation]:
        """Evaluates structured signals against department-specific guarantees."""
        guarantee_ids = {g.guarantee_id for g in contract.guarantees if g.verifiable}
        violations = []
        for signal in signals:
            if signal.guarantee_id in guarantee_ids and signal.severity_hint != "low":
                violations.append(BehaviorViolation(
                    department=contract.department,
                    guarantee_id=signal.guarantee_id,
                    reason=signal.reason,
                    severity=signal.severity_hint,
                    source_signal_ids=[signal.signal_id]
                ))
        return violations

    def audit_maes_events(self, events: List[MinimumAuditableEvent], raw_payloads: List[str] = None) -> ISOAuditRecord:
        """
        Oracle Sentinel v1.3 Integration:
        Performs event chain audits, secret scanning, simulation leakage checks,
        and generates a machine-actionable ISO compliance report.
        """
        # 1. Event Chain & Signature Auditing
        findings = self.compliance_auditor.verify_event_chain(events)
        
        # 2. Secret Redaction Auditing (if raw data payloads provided)
        if raw_payloads and len(raw_payloads) == len(events):
            for event, payload in zip(events, raw_payloads):
                redaction_findings = self.compliance_auditor.check_secret_redaction(event, payload)
                findings.extend(redaction_findings)

        # 3. Simulation Pollution Auditing
        pollution_findings = self.compliance_auditor.audit_simulation_ledger_separation(events)
        findings.extend(pollution_findings)

        # 4. Generate Final Compliance Audit Report
        return self.compliance_auditor.generate_iso_audit_report(events, findings)
