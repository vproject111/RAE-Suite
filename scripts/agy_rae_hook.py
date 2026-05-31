import sys
import os
import json

# Dynamic RAE-Core Path Discovery
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Try to find RAE-core relative to the current workspace structure
RAE_CORE_PATH = os.environ.get("RAE_CORE_PATH")
if not RAE_CORE_PATH:
    # Attempt to locate within the standard Silicon Oracle structure
    potential_path = os.path.join(SCRIPT_DIR, "..", "RAE-Suite/packages/rae-agentic-memory/rae-core")
    if os.path.exists(potential_path):
        RAE_CORE_PATH = potential_path

if RAE_CORE_PATH and RAE_CORE_PATH not in sys.path:
    sys.path.append(RAE_CORE_PATH)

from rae_core.utils.enterprise_guard import RAE_Enterprise_Foundation

def main():
    # RAE_Enterprise_Foundation handles intelligent project/tenant detection
    # via RAEContextLocator within RAEMemoryBridge
    foundation = RAE_Enterprise_Foundation("antigravity-cli")
    
    if len(sys.argv) < 2:
        return

    event_type = sys.argv[1] # e.g. "before_tool_call"
    details = sys.argv[2:]
    
    # RAE-First: Delegate layer and strategy decisions to RAE Core
    # We pass None for layer to let RAE Engine decide based on content/rules
    # We pass all available context in metadata
    foundation.bridge.save_event(
        content=f"AGY Event: {event_type} | Data: {' '.join(details)}",
        human_label=f"[AGY] {event_type.replace('_', ' ').title()}",
        layer=None,  # <--- RAE DECIDES THE LAYER
        metadata={
            "source": "antigravity_hook", 
            "event_type": event_type,
            "raw_args": details,
            "orchestrator_strategy": "RAE-First",
            "info_class": "internal", # Default class
            "governance": {
                "pattern_type": "orchestrator_event",
                "fields": {
                    "orchestrator": "antigravity-cli",
                    "event": event_type
                }
            }
        }
    )

if __name__ == "__main__":
    main()
