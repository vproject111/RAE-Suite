import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

try:
    from rae_contracts import (
        CapabilityContract,
        PolicyBundle,
        RiskAssessment,
        ExecutionReceipt,
        TaskState
    )
    print("✅ All Iteration 1 contracts successfully imported!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ An error occurred: {e}")
