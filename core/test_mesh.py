import pytest
import sys
import os
import time
from datetime import datetime, timedelta

# Ensure src is in sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from mesh.mesh_peer_registry import MeshPeerRegistry
from mesh.consent_manager import ConsentManager
from mesh.exporter import MeshExporter
from mesh.importer import MeshImporter
from mesh.exchange_envelope import ExchangeEnvelopeFactory

from rae_core.models.mesh import MeshPeer, ConsentGrant, MeshExchangeEnvelope
from rae_core.models.improvement import InsightPack, FailurePatternPack

def test_mesh_peer_registry():
    registry = MeshPeerRegistry()
    peer = MeshPeer(peer_id="peer-1", name="RAE Branch 1", endpoint="http://branch1:8000")
    
    registry.register_peer(peer)
    assert registry.get_peer("peer-1") == peer
    assert len(registry.list_peers()) == 1


def test_consent_manager():
    manager = ConsentManager()
    
    # 1. Valid Grant
    grant = ConsentGrant(grant_id="g-1", peer_id="peer-1", scope=["InsightPack"], ttl_days=5)
    manager.add_grant(grant)
    assert manager.is_valid(grant, "peer-1")
    
    # 2. Peer mismatch
    assert not manager.is_valid(grant, "peer-2")
    
    # 3. Expiry
    expired_grant = ConsentGrant(grant_id="g-2", peer_id="peer-1", scope=["InsightPack"], ttl_days=-1)
    assert not manager.is_valid(expired_grant, "peer-1")


def test_mesh_exporter_and_importer():
    consent_mgr = ConsentManager()
    exporter = MeshExporter(consent_mgr)
    importer = MeshImporter(current_instance_id="peer-1")
    
    peer = MeshPeer(peer_id="peer-1", name="Branch 1", endpoint="http://1.1.1.1")
    grant = ConsentGrant(grant_id="g-1", peer_id="peer-1", scope=["InsightPack"])
    consent_mgr.add_grant(grant)
    
    # Create allowed pack
    pack = InsightPack(pack_id="pack-1", insights=[{"metric": "latency", "val": 12.0}], recommendations=["Optimize cache"])
    
    # Export
    envelope = exporter.export(pack, peer, grant)
    assert isinstance(envelope, MeshExchangeEnvelope)
    assert envelope.pack_type == "InsightPack"
    
    # Import
    imported_data = importer.import_envelope(envelope)
    assert imported_data["pack_id"] == "pack-1"
    assert imported_data["provenance"]["source_instance"] == "rae-suite-main"


def test_mesh_exporter_blocked_types():
    consent_mgr = ConsentManager()
    exporter = MeshExporter(consent_mgr)
    
    peer = MeshPeer(peer_id="peer-1", name="Branch 1", endpoint="http://1.1.1.1")
    grant = ConsentGrant(grant_id="g-1", peer_id="peer-1", scope=["InsightPack"])
    consent_mgr.add_grant(grant)
    
    class BadPack:
        pack_id = "bad"
        
    with pytest.raises(ValueError, match="is not allowed for Mesh export"):
        exporter.export(BadPack(), peer, grant)


def test_mesh_exporter_leakage_block():
    consent_mgr = ConsentManager()
    exporter = MeshExporter(consent_mgr)
    
    peer = MeshPeer(peer_id="peer-1", name="Branch 1", endpoint="http://1.1.1.1")
    grant = ConsentGrant(grant_id="g-1", peer_id="peer-1", scope=["InsightPack"])
    consent_mgr.add_grant(grant)
    
    # Pack containing blocked keyword "secret"
    pack = InsightPack(pack_id="pack-1", insights=[{"auth_token_secret": "my-secret-key"}], recommendations=[])
    
    with pytest.raises(ValueError, match="Payload contains sensitive or restricted information"):
        exporter.export(pack, peer, grant)
