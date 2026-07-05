# src/mesh/exporter.py

"""
RAE Mesh Exporter — zasady wymiany:

CO MOŻNA EKSPORTOWAĆ (domyślnie):
  - InsightPack (zatwierdzone przez Lab)
  - FailurePatternPack (zanonimizowane)
  - BenchmarkSuite
  - BehaviorContractPack
  - PolicyPack

CZEGO NIE WOLNO EKSPORTOWAĆ (hard block):
  - Pełny memory store
  - Surowe dane klientów
  - Sekrety i tokeny
  - Wrażliwe logi bez anonimizacji
  - Prywatne eksperymenty bez ConsentGrant

KAŻDA WYMIANA WYMAGA:
  - ConsentGrant z scope i TTL
  - provenance (skąd pochodzi pack)
  - sensitivity_label
  - contract_version
"""

import uuid
import logging
from typing import Union, Dict, Any
from datetime import datetime, timedelta, timezone
from rae_core.models.mesh import MeshExchangeEnvelope, ConsentGrant, MeshPeer
from rae_core.models.improvement import InsightPack, FailurePatternPack

logger = logging.getLogger(__name__)

ALLOWED_PACK_TYPES = {InsightPack, FailurePatternPack}
BLOCKED_KEYWORDS = ["secret", "token", "password", "raw_memory", "customer_data"]

class MeshExporter:
    def __init__(self, consent_manager):
        self.consent = consent_manager

    def _contains_sensitive_data(self, data: Dict[str, Any]) -> bool:
        """
        Recursively scans dict payload for blocked keywords or sensitive info.
        """
        data_str = str(data).lower()
        for kw in BLOCKED_KEYWORDS:
            if kw in data_str:
                logger.warning(f"mesh_exporter: Blocked sensitive content. Found keyword: '{kw}'")
                return True
        return False

    def export(
        self,
        pack: Union[InsightPack, FailurePatternPack],
        target_peer: MeshPeer,
        consent_grant: ConsentGrant
    ) -> MeshExchangeEnvelope:
        if type(pack) not in ALLOWED_PACK_TYPES:
            raise ValueError(f"Pack type {type(pack)} is not allowed for Mesh export.")

        if not self.consent.is_valid(consent_grant, target_peer.peer_id):
            raise PermissionError(f"No valid ConsentGrant for peer {target_peer.peer_id}")

        # Check the payload contents for leakage
        payload = pack.model_dump() if hasattr(pack, "model_dump") else pack.dict()
        if self._contains_sensitive_data(payload):
            raise ValueError("Export blocked: Payload contains sensitive or restricted information.")

        # Determine provenance
        provenance = {
            "source_instance": "rae-suite-main",
            "compiled_at": datetime.now(timezone.utc).isoformat(),
            "operator_role": "lab_compiler"
        }

        expires_at = datetime.now(timezone.utc) + timedelta(days=consent_grant.ttl_days or 30)

        envelope = MeshExchangeEnvelope(
            envelope_id=str(uuid.uuid4()),
            source_instance="rae-suite-main",
            target_peer_id=target_peer.peer_id,
            pack_type=type(pack).__name__,
            pack_id=pack.pack_id,
            consent_ref=consent_grant.grant_id,
            expires_at=expires_at,
            sensitivity_label="internal",
            payload_data=payload,
            provenance=provenance,
            contract_version="1.0.0"
        )
        
        logger.info(f"mesh_exporter: Exported envelope {envelope.envelope_id} for peer {target_peer.peer_id}")
        return envelope
