from enum import Enum
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field

class AuditFindingSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AuditFinding(BaseModel):
    schema_version: str = "1.0"
    finding_id: str = Field(..., description="Unique compliance violation identifier")
    trace_id: Optional[str] = Field(None, description="Associated trace thread")
    control_id: Optional[str] = Field(None, description="ISO standard control reference, e.g. A.12.4.1")
    severity: AuditFindingSeverity = Field(..., description="Violation severity score")
    finding_type: str = Field(..., description="Violation type, e.g., missing_receipt, signature_gap")
    description: str = Field(..., description="Human and machine readable details of the violation")
    related_event_ids: List[str] = Field(default_factory=list, description="List of related MAES events")
    remediation_required: bool = Field(True, description="Whether immediate correction is needed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
