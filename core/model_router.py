import logging
from typing import Dict, List, Any, Tuple
from pydantic import BaseModel
from rae_contracts import RiskClass

logger = logging.getLogger(__name__)

class ModelProfile(BaseModel):
    model_name: str
    context_window: int
    provider: str
    is_local: bool
    cost_input_1k: float  # cost in USD per 1,000 input tokens
    cost_output_1k: float  # cost in USD per 1,000 output tokens
    latency_p50_ms: float
    quality_score: float  # scaled 0.0 to 1.0
    supports_json_schema: bool
    supports_tools: bool
    max_risk_class: RiskClass

class ModelRouter:
    """
    Implements the Token-Budget Routing pattern.
    Manages ModelRegistry and selects the optimal model based on cost, latency, and RiskClass.
    Enforces the Trójwarstwowy Sąd (Quality Tribunal Tiers 1-3) with local model priority.
    """
    def __init__(self):
        self.registry: Dict[str, ModelProfile] = {}
        self._load_default_registry()

    def _load_default_registry(self):
        # Local models on Node 3 (Piotrek)
        self.registry["llama-3.1-8b"] = ModelProfile(
            model_name="llama-3.1-8b",
            context_window=128000,
            provider="ollama/piotrek",
            is_local=True,
            cost_input_1k=0.0,
            cost_output_1k=0.0,
            latency_p50_ms=450.0,
            quality_score=0.72,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R2
        )
        self.registry["qwen-2.5-7b"] = ModelProfile(
            model_name="qwen-2.5-7b",
            context_window=32000,
            provider="ollama/piotrek",
            is_local=True,
            cost_input_1k=0.0,
            cost_output_1k=0.0,
            latency_p50_ms=400.0,
            quality_score=0.70,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R2
        )
        self.registry["mistral-7b-v0.3"] = ModelProfile(
            model_name="mistral-7b-v0.3",
            context_window=32000,
            provider="ollama/piotrek",
            is_local=True,
            cost_input_1k=0.0,
            cost_output_1k=0.0,
            latency_p50_ms=500.0,
            quality_score=0.68,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R2
        )
        self.registry["mixtral-8x7b"] = ModelProfile(
            model_name="mixtral-8x7b",
            context_window=32000,
            provider="ollama/piotrek",
            is_local=True,
            cost_input_1k=0.0,
            cost_output_1k=0.0,
            latency_p50_ms=900.0,
            quality_score=0.82,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R4
        )
        self.registry["llama-3.1-70b-instruct"] = ModelProfile(
            model_name="llama-3.1-70b-instruct",
            context_window=128000,
            provider="ollama/piotrek",
            is_local=True,
            cost_input_1k=0.0,
            cost_output_1k=0.0,
            latency_p50_ms=1200.0,
            quality_score=0.85,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R4
        )
        self.registry["deepseek-coder-33b"] = ModelProfile(
            model_name="deepseek-coder-33b",
            context_window=16000,
            provider="ollama/piotrek",
            is_local=True,
            cost_input_1k=0.0,
            cost_output_1k=0.0,
            latency_p50_ms=850.0,
            quality_score=0.83,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R4
        )

        # Commercial models (API based, expensive)
        self.registry["gemini-1.5-pro"] = ModelProfile(
            model_name="gemini-1.5-pro",
            context_window=2000000,
            provider="google",
            is_local=False,
            cost_input_1k=0.00125,
            cost_output_1k=0.00375,
            latency_p50_ms=1500.0,
            quality_score=0.94,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R6
        )
        self.registry["gpt-4o"] = ModelProfile(
            model_name="gpt-4o",
            context_window=128000,
            provider="openai",
            is_local=False,
            cost_input_1k=0.005,
            cost_output_1k=0.015,
            latency_p50_ms=1100.0,
            quality_score=0.93,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R6
        )
        self.registry["claude-3-5-sonnet"] = ModelProfile(
            model_name="claude-3-5-sonnet",
            context_window=2000000,
            provider="anthropic",
            is_local=False,
            cost_input_1k=0.003,
            cost_output_1k=0.015,
            latency_p50_ms=1300.0,
            quality_score=0.95,
            supports_json_schema=True,
            supports_tools=True,
            max_risk_class=RiskClass.R6
        )

    def route_task(self, risk_class: RiskClass, expected_tokens: int = 5000) -> str:
        """
        Routes the task to the cheapest model that meets the risk profile.
        """
        # Prioritize local models for low/medium risk tasks
        if risk_class in [RiskClass.R0, RiskClass.R1, RiskClass.R2]:
            return "llama-3.1-8b"
        elif risk_class in [RiskClass.R3, RiskClass.R4]:
            return "mixtral-8x7b"
        else:
            return "gemini-1.5-pro"

    def get_tribunal_quorum_models(self, tier: int) -> List[str]:
        """
        Quality Tribunal: returns 3 models for quorum voting.
        Tier 1: Partial Court (100% Local models)
        Tier 2: Appellate Court (100% Local strong models)
        Tier 3: Supreme Court (Advanced API-based models)
        """
        if tier == 1:
            return ["llama-3.1-8b", "qwen-2.5-7b", "mistral-7b-v0.3"]
        elif tier == 2:
            return ["mixtral-8x7b", "llama-3.1-70b-instruct", "deepseek-coder-33b"]
        elif tier == 3:
            return ["gemini-1.5-pro", "gpt-4o", "claude-3-5-sonnet"]
        else:
            raise ValueError(f"Unknown Quality Tribunal Tier: {tier}")
