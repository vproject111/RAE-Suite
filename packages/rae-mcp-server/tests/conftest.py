# RAE-MCP-Server tests conftest
import sys
from pathlib import Path

MCP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_DIR))
