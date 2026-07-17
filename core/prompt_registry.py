import hashlib
import threading
from typing import Dict, Optional, Tuple

class FederatedPromptRegistry:
    """
    Implements the Federated Message Templates pattern.
    Allows layering prompts from Base -> Org -> Team -> Feature
    and compiles them into a deterministic, hashed prompt string.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self.base_templates: Dict[str, str] = {}
        self.org_templates: Dict[str, Dict[str, str]] = {}
        self.team_templates: Dict[str, Dict[str, str]] = {}
        self.feature_templates: Dict[str, Dict[str, str]] = {}

    def register_base(self, template: str):
        if not template.strip():
            raise ValueError("Template content cannot be empty")
        with self._lock:
            if "system" in self.base_templates:
                raise RuntimeError("Base template is frozen and cannot be modified")
            self.base_templates["system"] = template

    def register_org(self, org: str, section: str, content: str):
        if not content.strip():
            raise ValueError("Content cannot be empty")
        sanitized_org = org.replace('\n', '').replace('\r', '')
        sanitized_sec = section.replace('\n', '').replace('\r', '')
        with self._lock:
            if sanitized_org not in self.org_templates:
                self.org_templates[sanitized_org] = {}
            self.org_templates[sanitized_org][sanitized_sec] = content

    def register_team(self, team: str, section: str, content: str):
        if not content.strip():
            raise ValueError("Content cannot be empty")
        sanitized_team = team.replace('\n', '').replace('\r', '')
        sanitized_sec = section.replace('\n', '').replace('\r', '')
        with self._lock:
            if sanitized_team not in self.team_templates:
                self.team_templates[sanitized_team] = {}
            self.team_templates[sanitized_team][sanitized_sec] = content

    def register_feature(self, feature: str, section: str, content: str):
        if not content.strip():
            raise ValueError("Content cannot be empty")
        sanitized_feat = feature.replace('\n', '').replace('\r', '')
        sanitized_sec = section.replace('\n', '').replace('\r', '')
        with self._lock:
            if sanitized_feat not in self.feature_templates:
                self.feature_templates[sanitized_feat] = {}
            self.feature_templates[sanitized_feat][sanitized_sec] = content

    def compile_prompt(self, feature: str, team: Optional[str] = None, org: Optional[str] = None) -> Tuple[str, str]:
        """
        Compiles the prompt from Base -> Org -> Team -> Feature.
        Returns a tuple of (compiled_prompt_str, prompt_hash).
        """
        with self._lock:
            sections = {"system": [self.base_templates.get("system", "")]}

            if org and org in self.org_templates:
                for sec, content in self.org_templates[org].items():
                    if sec not in sections:
                        sections[sec] = []
                    sections[sec].append(content)

            if team and team in self.team_templates:
                for sec, content in self.team_templates[team].items():
                    if sec not in sections:
                        sections[sec] = []
                    sections[sec].append(content)

            if feature in self.feature_templates:
                for sec, content in self.feature_templates[feature].items():
                    if sec not in sections:
                        sections[sec] = []
                    sections[sec].append(content)

            # Format compiled prompt deterministically
            compiled_parts = []
            for sec in sorted(sections.keys()):
                joined_content = "\n".join(sections[sec]).strip()
                if joined_content:
                    sanitized_sec = sec.replace('\n', '').replace('\r', '')
                    compiled_parts.append(f"=== {sanitized_sec.upper()} ===\n{joined_content}")
            
            compiled_prompt = "\n\n".join(compiled_parts)
            
            # Salt the hash with context to prevent collisions across different features/orgs/teams
            salt = f"{org or 'default'}:{team or 'default'}:{feature}"
            hash_input = f"{salt}\n{compiled_prompt}"
            prompt_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
            
            return compiled_prompt, prompt_hash
