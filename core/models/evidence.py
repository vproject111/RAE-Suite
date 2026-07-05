import time
from typing import List
from pydantic import BaseModel, Field

class ActionRecord(BaseModel):
    department: str
    role: str
    action_type: str
    goal: str
    tools_used: List[str] = Field(default_factory=list)
    trace_id: str
    timestamp: float = Field(default_factory=time.time)
