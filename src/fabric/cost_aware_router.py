from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class CostAwareRouter:
    RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    def route(
        self,
        capability_id: str,
        agents: List[dict],
        max_risk: str = "high",
        weights: Optional[dict] = None,
    ) -> Optional[dict]:
        candidates = [a for a in agents if capability_id in a.get("capabilities", [])]
        
        allowed = [
            c for c in candidates 
            if self.RISK_ORDER.get(c.get("risk_class", "low"), 0) <= self.RISK_ORDER.get(max_risk, 2)
        ]

        if not allowed:
            return None

        if weights and all(k in weights for k in ("alpha", "beta", "gamma")):
            alpha = float(weights.get("alpha", 0.4))
            beta = float(weights.get("beta", 0.3))
            gamma = float(weights.get("gamma", 0.3))
            allowed.sort(
                key=lambda x: (
                    self.RISK_ORDER.get(x.get("risk_class", "low"), 0),
                    (alpha * float(x.get("failure_rate_30d", 0.0)))
                    + (beta * float(x.get("latency_p50_s", 1.0)))
                    + (gamma * float(x.get("estimated_ncu", 0.0))),
                )
            )
            return allowed[0]

        # Sort candidate agents by risk, cost (NCU), failure rate and latency
        allowed.sort(key=lambda x: (
            self.RISK_ORDER.get(x.get("risk_class", "low"), 0),
            x.get("estimated_ncu", 0.0),
            x.get("failure_rate_30d", 0.0),
            x.get("latency_p50_s", float("inf"))
        ))

        return allowed[0]

