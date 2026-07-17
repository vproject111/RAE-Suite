import uuid
import re
from typing import Dict, Tuple, Optional

class TraceContextPropagator:
    """
    Implements W3C Trace Context propagation for OTEL Trace Propagation.
    Translates trace_ids between RAE-Suite components and formats the 'traceparent' header.
    """
    @staticmethod
    def _validate_hex(id_str: str, expected_length: int) -> str:
        # Strip prefixes and non-hex chars
        clean = re.sub(r'[^0-9a-fA-F]', '', id_str.replace("trace-", ""))
        if len(clean) != expected_length or not clean:
            # Fallback to a fresh valid UUID segment/hex
            new_id = uuid.uuid4().hex[:expected_length]
            return new_id.lower()
        return clean.lower()

    @staticmethod
    def inject(trace_id: str, span_id: Optional[str] = None, sampled: bool = True) -> Dict[str, str]:
        # Normalize trace_id to 32 hex characters with strict validation
        clean_trace_id = TraceContextPropagator._validate_hex(trace_id, 32)
        
        # Normalize/generate span_id to 16 hex characters with strict validation
        if not span_id:
            span_id = uuid.uuid4().hex[:16].lower()
        else:
            span_id = TraceContextPropagator._validate_hex(span_id, 16)
            
        flags = "01" if sampled else "00"
        traceparent = f"00-{clean_trace_id}-{span_id}-{flags}"
        return {"traceparent": traceparent}

    @staticmethod
    def extract(headers: Dict[str, str]) -> Tuple[str, str]:
        traceparent = headers.get("traceparent") or headers.get("Traceparent")
        if not traceparent:
            # Return fresh generated values if missing
            new_trace = f"trace-{uuid.uuid4()}"
            return new_trace, uuid.uuid4().hex[:16].lower()
            
        match = re.match(r"^00-([0-9a-fA-F]{32})-([0-9a-fA-F]{16})-[0-9a-fA-F]{2}$", traceparent)
        if not match:
            new_trace = f"trace-{uuid.uuid4()}"
            return new_trace, uuid.uuid4().hex[:16].lower()
            
        trace_id_hex = match.group(1).lower()
        span_id_hex = match.group(2).lower()
        
        # Restore grouping to match RAE trace-uuid format
        formatted_trace_id = f"trace-{trace_id_hex[:8]}-{trace_id_hex[8:12]}-{trace_id_hex[12:16]}-{trace_id_hex[16:20]}-{trace_id_hex[20:]}"
        return formatted_trace_id, span_id_hex
