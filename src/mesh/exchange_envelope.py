import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from rae_core.models.mesh import MeshExchangeEnvelope

class ExchangeEnvelopeFactory:
    """
    Helper factory for building MeshExchangeEnvelopes.
    """
    @staticmethod
    def create_envelope(
        target_peer_id: str,
        pack_type: str,
        pack_id: str,
        consent_ref: str,
        payload_data: Dict[str, Any],
        provenance: Dict[str, Any],
        ttl_days: int = 30
    ) -> MeshExchangeEnvelope:
        return MeshExchangeEnvelope(
            envelope_id=str(uuid.uuid4()),
            source_instance="rae-suite-main",
            target_peer_id=target_peer_id,
            pack_type=pack_type,
            pack_id=pack_id,
            consent_ref=consent_ref,
            expires_at=datetime.utcnow() + timedelta(days=ttl_days),
            sensitivity_label="internal",
            payload_data=payload_data,
            provenance=provenance,
            contract_version="1.0.0"
        )
