import time
from pydantic import BaseModel, Field

class FailureLearningRecord(BaseModel):
    failure_id: str
    task_id: str
    trace_id: str
    error_message: str
    pattern: str
    action_taken: str
    timestamp: float = Field(default_factory=time.time)
