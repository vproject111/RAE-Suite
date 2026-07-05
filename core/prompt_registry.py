import hashlib
from typing import Dict, Optional, Tuple

class FederatedPromptRegistry:
    """
    Implements the Federated Message Templates pattern.
    Allows layering prompts from Base -> Org -> Team -> Feature
    and compiles them into a deterministic, hashed prompt string.
    """
    def __init__(self):
        self.base_templates: Dict[str, str] = {}
        self.org_templates: Dict[str, Dict[str, str]] = {}
        self.team_templates: Dict[str, Dict[str, str]] = {}
        self.feature_templates: Dict[str, Dict[str, str]] = {}

    def register_base(self, template: str):
        self.base_templates["system"] = template

    def register_org(self, org: str, section: str, content: str):
        if org not in self.org_templates:
            self.org_templates[org] = {}
        self.org_templates[org][section] = content

    def register_team(self, team: str, section: str, content: str):
        if team not in self.team_templates:
            self.team_templates[team] = {}
        self.team_templates[team][section] = content

    def register_feature(self, feature: str, section: str, content: str):
        if feature not in self.feature_templates:
            self.feature_templates[feature] = {}
        self.feature_templates[feature][section] = content

    def compile_prompt(self, feature: str, team: Optional[str] = None, org: Optional[str] = None) -> Tuple[str, str]:
        """
        Compiles the prompt from Base -> Org -> Team -> Feature.
        Returns a tuple of (compiled_prompt_str, prompt_hash).
        """
        sections = {"system": self.base_templates.get("system", "")}

        if org and org in self.org_templates:
            for sec, content in self.org_templates[org].items():
                sections[sec] = (sections.get(sec, "") + "\n" + content).strip()

        if team and team in self.team_templates:
            for sec, content in self.team_templates[team].items():
                sections[sec] = (sections.get(sec, "") + "\n" + content).strip()

        if feature in self.feature_templates:
            for sec, content in self.feature_templates[feature].items():
                sections[sec] = (sections.get(sec, "") + "\n" + content).strip()

        # Format compiled prompt deterministically
        compiled_parts = []
        for sec in sorted(sections.keys()):
            content = sections[sec].strip()
            if content:
                compiled_parts.append(f"=== {sec.upper()} ===\n{content}")
        
        compiled_prompt = "\n\n".join(compiled_parts)
        prompt_hash = hashlib.sha256(compiled_prompt.encode('utf-8')).hexdigest()
        
        return compiled_prompt, prompt_hash
