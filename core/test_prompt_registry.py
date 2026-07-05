from core.prompt_registry import FederatedPromptRegistry

def test_federated_prompt_compilation():
    registry = FederatedPromptRegistry()
    
    # 1. Base template
    registry.register_base("Base system instructions.")
    
    # 2. Org level additions
    registry.register_org("dreamsoft", "security", "Org-level security principles.")
    
    # 3. Team level additions
    registry.register_team("core-team", "guidelines", "Team-level coding guidelines.")
    
    # 4. Feature level additions
    registry.register_feature("aea-0", "system", "Feature-specific context.")
    registry.register_feature("aea-0", "security", "Strict sandbox enforcement.")
    
    # Compile
    prompt, prompt_hash = registry.compile_prompt("aea-0", "core-team", "dreamsoft")
    
    assert "Base system instructions." in prompt
    assert "Org-level security principles." in prompt
    assert "Team-level coding guidelines." in prompt
    assert "Feature-specific context." in prompt
    assert "Strict sandbox enforcement." in prompt
    assert len(prompt_hash) == 64  # SHA-256 length
    
    # Check deterministic behavior
    prompt2, prompt_hash2 = registry.compile_prompt("aea-0", "core-team", "dreamsoft")
    assert prompt == prompt2
    assert prompt_hash == prompt_hash2
