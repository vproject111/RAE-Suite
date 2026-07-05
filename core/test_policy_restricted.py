from core.policy_checker import RiskClassifier, PolicyChecker
from rae_contracts import RiskClass, DecisionType

def test_restricted_data_isolation():
    classifier = RiskClassifier()
    checker = PolicyChecker()
    
    # 1. Restricted info in working layer -> ALLOWED / Normal Risk
    payload_ok = {
        "info_class": "restricted",
        "layer": "working"
    }
    assessment_ok = classifier.assess_risk("trace-1", "sterile read", payload_ok)
    # The risk should not be R6
    assert assessment_ok.risk_class != RiskClass.R6
    decision_ok = checker.evaluate_policy(assessment_ok)
    assert decision_ok == DecisionType.ALLOW

    # 2. Restricted info in non-working layer (e.g. episodic) -> BLOCKED / Risk R6 / Quarantine
    payload_bad = {
        "info_class": "restricted",
        "layer": "episodic"
    }
    assessment_bad = classifier.assess_risk("trace-2", "sterile read", payload_bad)
    assert assessment_bad.risk_class == RiskClass.R6
    assert "RESTRICTED data processed outside Working layer" in assessment_bad.reasons[0]
    decision_bad = checker.evaluate_policy(assessment_bad)
    assert decision_bad == DecisionType.QUARANTINE
