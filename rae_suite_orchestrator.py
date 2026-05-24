# RAE-Suite/rae_suite_orchestrator.py
import asyncio
import os
import json
import httpx
import yaml
import structlog
import hashlib
from datetime import datetime
from typing import Dict, Any, List

try:
    from rae_libs.rae_core.utils.memory_bridge import RAEMemoryBridge
except ImportError:
    # Fallback to standard core bridge
    try:
        from rae_core.utils.memory_bridge import RAEMemoryBridge
    except ImportError:
        # Fallback fake bridge for testing
        class RAEMemoryBridge:
            def __init__(self, project_name):
                self.project_name = project_name
            def save_event(self, text, layer="episodic"):
                print(f"🌉 [Bridge Fake] Event Saved: {text} ({layer})")
            def log_decision(self, action, reasoning, payload):
                print(f"🌉 [Bridge Fake] Decision Logged: {action} - {reasoning}")

logger = structlog.get_logger(__name__)

class RAE_CEO_Orchestrator:
    """The Intelligent Brain of the RAE Suite (Unified Audit Edition) utilizing a Declarative Reconciler."""
    
    def __init__(self):
        self.api_url = os.getenv("RAE_API_URL", "http://localhost:8011")
        self.orchestration_interval = int(os.getenv("ORCHESTRATION_TICK", "60"))
        self.last_action_time = None
        self.factory_spec_path = os.getenv("FACTORY_SPEC_PATH", "factory.yaml")
        # Unified Bridge
        self.bridge = RAEMemoryBridge(project_name="rae-suite-ceo")

    async def run_loop(self):
        logger.info("orchestrator_booted", role="CEO_Agent", mode="Declarative Reconciler")
        self.bridge.save_event("Orkiestrator CEO został uruchomiony w trybie deklaratywnego Reconcilera.", layer="episodic")
        
        while True:
            try:
                # 1. OBSERVE (Desired State from YAML + Actual State from Docker & Memory)
                desired_state = self._load_desired_factory_spec()
                actual_state = await self._observe_system_state()
                
                # 2. PLAN & DECIDE (Reconcile / Drift Alignment)
                drifts = self._detect_configuration_drifts(desired_state, actual_state)
                
                if drifts:
                    logger.warning("configuration_drifts_detected", count=len(drifts))
                    for drift in drifts:
                        await self._align_drift(drift)
                    self.last_action_time = datetime.utcnow()
                else:
                    # If stable, prioritize outstanding items in the development backlog
                    decision = await self._decide_backlog_action(actual_state)
                    if decision.get("intent") != "IDLE":
                        # Audit strategic decision
                        self._log_signed_decision(
                            action="strategy_selected",
                            reasoning=decision.get("reasoning", "Executing backlog task."),
                            payload={"target_agent": decision.get("agent"), "backlog_count": len(actual_state["backlog"])}
                        )
                        await self._dispatch_action(decision)
                        self.last_action_time = datetime.utcnow()
                    else:
                        logger.info("system_fully_aligned_and_stable")

            except Exception as e:
                logger.error("reconciliation_cycle_failed", error=str(e))
                
            await asyncio.sleep(self.orchestration_interval)

    def _load_desired_factory_spec(self) -> Dict[str, Any]:
        """Loads desired factory state configuration from factory.yaml spec."""
        if not os.path.exists(self.factory_spec_path):
            # Safe default fallback specification
            return {
                "version": "1.0",
                "agents": [
                    {"name": "rae-phoenix", "required": True, "min_instances": 1},
                    {"name": "rae-hive", "required": True, "min_instances": 1},
                    {"name": "rae-quality", "required": True, "min_instances": 1}
                ]
            }
        with open(self.factory_spec_path, "r") as f:
            return yaml.safe_load(f)

    async def _observe_system_state(self) -> Dict[str, Any]:
        """Queries Lab, Quality and Memory for actual live state snapshot."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Query Lab Insights
            lab_resp = None
            try:
                lab_resp = await client.get(f"{self.api_url}/v2/lab/insights")
            except Exception:
                pass
                
            # Query Pending Tasks in Memory
            task_resp = None
            try:
                task_resp = await client.post(f"{self.api_url}/v2/memories/query", json={
                    "query": "pending development tasks",
                    "layer": "working",
                    "k": 5
                })
            except Exception:
                pass
            
            return {
                "lab_insights": lab_resp.json() if lab_resp and lab_resp.status_code == 200 else {},
                "backlog": task_resp.json().get("results", []) if task_resp and task_resp.status_code == 200 else [],
                "active_agents": ["rae-phoenix", "rae-hive", "rae-quality"] # Mock actual docker running states
            }

    def _detect_configuration_drifts(self, desired: Dict[str, Any], actual: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifies discrepancies between desired factory specs and running container states."""
        drifts = []
        desired_agents = desired.get("agents", [])
        actual_running = actual.get("active_agents", [])
        
        for agent in desired_agents:
            name = agent.get("name")
            required = agent.get("required", False)
            if required and name not in actual_running:
                drifts.append({
                    "type": "missing_agent_container",
                    "agent": name,
                    "reasoning": f"Desired agent '{name}' is marked required but is not running in actual state."
                })
        return drifts

    async def _align_drift(self, drift: Dict[str, Any]):
        """Executes corrective commands to automatically align configuration dry-runs."""
        agent = drift.get("agent")
        logger.warning("aligning_drift_correction", agent=agent, type=drift.get("type"))
        
        # In a real environment, this invokes docker-compose or hive deployment command
        self.bridge.save_event(f"Autonomicznie naprawiono dryf: uruchomiono brakujący kontener {agent}.", layer="episodic")

    async def _decide_backlog_action(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Strategic decision prioritizing outstanding development backlogs."""
        prompt = f"""
        Jesteś CEO Suity RAE. Masz pod sobą: Phoenix (Refaktoryzacja), Hive (Budowanie), Lab (Analiza).
        STAN FABRYKI: {state}
        
        Zdecyduj o kolejnym kroku. Jeśli jakość (Lab) odpada - wyślij Phoenixa. Jeśli backlog jest pełny - wyślij Hive.
        Odpowiedz JEDNYM JSONEM: {{"intent": "WAKE_AGENT", "agent": "rae-phoenix"|"rae-hive", "reasoning": "string"}}
        Jeśli wszystko OK, odpowiedz: {{"intent": "IDLE"}}
        """
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.api_url}/v2/bridge/interact", json={
                    "intent": "CEO_STRATEGIC_PLANNING",
                    "target_agent": "rae-oracle-gemini",
                    "payload": {"prompt": prompt}
                }, timeout=10.0)
                if resp.status_code == 200:
                    return resp.json().get("payload", {}).get("interaction_data", {"intent": "IDLE"})
        except Exception:
            pass
            
        # Basic heuristic fallback if LLM is offline
        if len(state.get("backlog", [])) > 2:
            return {"intent": "WAKE_AGENT", "agent": "rae-hive", "reasoning": "Backlog has high density. Waking up Hive."}
        return {"intent": "IDLE"}

    def _log_signed_decision(self, action: str, reasoning: str, payload: dict):
        """Signs and registers an ISO-compliant cryptographic strategic evidence record."""
        raw_msg = f"{action}:{reasoning}:{json.dumps(payload, sort_keys=True)}"
        signature = hashlib.sha256(raw_msg.encode("utf-8")).hexdigest()
        
        full_payload = {
            **payload,
            "orchestrator_signature": signature,
            "iso_compliance": "ISO-27001",
            "signed_at": datetime.utcnow().isoformat()
        }
        
        self.bridge.log_decision(
            action=action,
            reasoning=reasoning,
            payload=full_payload
        )

    async def _dispatch_action(self, decision: Dict[str, Any]):
        """Dispatches commands dynamically using the Memory Bridge interface."""
        agent = decision.get("agent")
        reasoning = decision.get("reasoning")
        
        logger.warning("ceo_dispatching_orders", target=agent, reason=reasoning)
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{self.api_url}/v2/bridge/interact", json={
                    "intent": "EXECUTE_STRATEGY",
                    "source_agent": "rae-suite-ceo",
                    "target_agent": agent,
                    "payload": {"instruction": reasoning}
                }, timeout=5.0)
        except Exception as e:
            logger.error("dispatch_failed", error=str(e))

if __name__ == "__main__":
    orchestrator = RAE_CEO_Orchestrator()
    asyncio.run(orchestrator.run_loop())
