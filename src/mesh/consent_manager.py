import time
import logging
from typing import Dict, Optional
from rae_core.models.mesh import ConsentGrant

logger = logging.getLogger(__name__)

class ConsentManager:
    """
    Manages and validates Consent Grants for Mesh knowledge exchange.
    """
    def __init__(self):
        self._grants: Dict[str, ConsentGrant] = {}

    def add_grant(self, grant: ConsentGrant):
        self._grants[grant.grant_id] = grant
        logger.info(f"consent_manager: Added ConsentGrant {grant.grant_id} for peer {grant.peer_id}")

    def get_grant(self, grant_id: str) -> Optional[ConsentGrant]:
        return self._grants.get(grant_id)

    def is_valid(self, grant: ConsentGrant, target_peer_id: str) -> bool:
        """
        Validates if the ConsentGrant is valid for the target peer and has not expired.
        """
        if grant.peer_id != target_peer_id:
            logger.warning(f"consent_manager: ConsentGrant {grant.grant_id} target peer mismatch: {grant.peer_id} vs {target_peer_id}")
            return False

        # Expiry Check
        now = time.time()
        expiry_time = grant.created_at + (grant.ttl_days * 86400)
        if now > expiry_time:
            logger.warning(f"consent_manager: ConsentGrant {grant.grant_id} expired {now - expiry_time:.1f}s ago")
            return False

        return True
