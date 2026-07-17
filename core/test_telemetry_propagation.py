import pytest
from core.telemetry_propagation import TraceContextPropagator

def test_trace_context_injection_and_extraction():
    original_trace_id = "trace-4bf92f35-77b3-4da6-a3ce-929d0e0e4736"
    span_id = "00f067aa0ba902b7"
    
    # Inject
    headers = TraceContextPropagator.inject(original_trace_id, span_id)
    assert "traceparent" in headers
    assert headers["traceparent"] == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    
    # Extract
    extracted_trace_id, extracted_span_id = TraceContextPropagator.extract(headers)
    assert extracted_trace_id == original_trace_id
    assert extracted_span_id == span_id

def test_trace_context_extraction_fallback():
    # Invalid headers
    headers = {"some-other-header": "value"}
    extracted_trace_id, extracted_span_id = TraceContextPropagator.extract(headers)
    
    assert extracted_trace_id.startswith("trace-")
    assert len(extracted_span_id) == 16
