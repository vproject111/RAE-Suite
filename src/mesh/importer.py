import logging
from datetime import datetime
from rae_core.models.mesh import MeshExchangeEnvelope
from rae_core.models.improvement import InsightPack, FailurePatternPack

logger = logging.getLogger(__name__)

class MeshImporter:
    """
    Imports and validates MeshExchangeEnvelopes from other RAE instances.
    Enforces provenance checks, TTL expiration, and contract integrity.
    """
    def __init__(self, current_instance_id: str = "rae-suite-main"):
        self.current_instance_id = current_instance_id

    def import_envelope(self, envelope: MeshExchangeEnvelope) -> dict:
        # 1. Target Peer Verification
        if envelope.target_peer_id != self.current_instance_id:
            raise ValueError(f"import_blocked: target_peer_id mismatch. Expected {self.current_instance_id}, got {envelope.target_peer_id}")

        # 2. TTL Expiry Check
        # Make sure comparison is timezone-naive or aware depending on inputs
        expires_at = envelope.expires_at
        if expires_at.tzinfo is not None:
            # Convert to naive UTC
            expires_at = expires_at.replace(tzinfo=None)
            
        if datetime.utcnow() > expires_at:
            raise ValueError(f"import_blocked: Envelope {envelope.envelope_id} has expired (expired at {envelope.expires_at})")

        # 3. Provenance & Contract Checks
        if not envelope.provenance or "source_instance" not in envelope.provenance:
            raise ValueError("import_blocked: Missing provenance metadata.")

        if envelope.contract_version != "1.0.0":
            raise ValueError(f"import_blocked: Unsupported contract version {envelope.contract_version}")

        # Reconstruct the pack
        pack_type = envelope.pack_type
        payload = envelope.payload_data

        logger.info(f"mesh_importer: Successfully imported envelope {envelope.envelope_id} of type {pack_type} from {envelope.source_instance}")
        return {
            "pack_type": pack_type,
            "pack_id": envelope.pack_id,
            "provenance": envelope.provenance,
            "data": payload
        }
