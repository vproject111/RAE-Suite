import logging
from typing import Dict, List, Optional
from rae_core.models.mesh import MeshPeer

logger = logging.getLogger(__name__)

class MeshPeerRegistry:
    """
    Registry for managing trusted RAE Mesh peers.
    """
    def __init__(self):
        self._peers: Dict[str, MeshPeer] = {}

    def register_peer(self, peer: MeshPeer):
        self._peers[peer.peer_id] = peer
        logger.info(f"mesh_peer_registry: Registered peer {peer.peer_id} ({peer.name})")

    def get_peer(self, peer_id: str) -> Optional[MeshPeer]:
        return self._peers.get(peer_id)

    def list_peers(self) -> List[MeshPeer]:
        return list(self._peers.values())
