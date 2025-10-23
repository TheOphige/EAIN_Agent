"""
metta_client.py

Simple client wrapper that exposes the high-level API the agent will use:
- assert_investor_profile(profile_atom) -> atom_id (simulated)
- assert_asset_atom(asset_atom) -> atom_id (simulated)
- evaluate_asset(asset_atom, investor_id) -> Decision dict
- batch_evaluate(assets, investor) -> list[Decision]

Currently implemented using metta_shim internally. Swap to HTTP client
for real MeTTa runtime easily.
"""
from typing import List, Dict
from src.utils.logger import log
from src.metta import metta_shim
from src.utils.helpers import timestamp_secs
import uuid

# In-memory atomstore for session / demo (simple dict)
ATOM_STORE: Dict[str, Dict] = {}

def _store_atom(atom: Dict) -> str:
    """
    Store atom in local in-memory store and return an id.
    Atom is enriched with a timestamp and generated id.
    """
    atom_id = f"atom_{uuid.uuid4().hex[:12]}"
    atom_copy = atom.copy()
    atom_copy["_id"] = atom_id
    atom_copy["_ts"] = timestamp_secs()
    ATOM_STORE[atom_id] = atom_copy
    log.debug(f"[METTA_CLIENT] Stored atom {atom_id}")
    return atom_id

def assert_investor_profile(profile: Dict) -> str:
    """
    Assert investor profile into our atomstore.
    Returns atom_id.
    """
    atom = {
        "type": "Investor",
        "profile": profile
    }
    atom_id = _store_atom(atom)
    return atom_id

def assert_asset_atom(asset: Dict) -> str:
    atom = {
        "type": "Asset",
        "asset": asset
    }
    atom_id = _store_atom(atom)
    return atom_id

def evaluate_asset_for_investor(asset: Dict, investor_profile: Dict, record_provenance: bool = True) -> Dict:
    """
    Evaluate single asset for a given investor_profile using metta_shim.
    Returns Decision dict from metta_shim.evaluate_asset.
    """
    # Store atoms for provenance traceability
    inv_atom_id = assert_investor_profile(investor_profile)
    asset_atom_id = assert_asset_atom(asset)

    # Call the shim to evaluate
    try:
        decision = metta_shim.evaluate_asset(investor_profile, asset, record_provenance=record_provenance)
    except Exception as e:
        log.error(f"metta_shim evaluation error: {e}")
        decision = {
            "asset": asset.get("symbol"),
            "decision": "deprioritize",
            "score": 0.0,
            "reason_tree": [{"rule": "metta_error", "note": str(e)}],
            "confidence": 0.0,
            "provenance": None,
            "timestamp": timestamp_secs()
        }

    # Enrich decision with atom references
    decision["_investor_atom"] = inv_atom_id
    decision["_asset_atom"] = asset_atom_id
    decision["_decision_id"] = f"decision_{uuid.uuid4().hex[:10]}"
    # Optionally store the decision as an atom as well
    ATOM_STORE[decision["_decision_id"]] = decision

    return decision

def batch_evaluate(assets: List[Dict], investor_profile: Dict, record_provenance: bool = True) -> List[Dict]:
    results = []
    for a in assets:
        try:
            res = evaluate_asset_for_investor(a, investor_profile, record_provenance=record_provenance)
            results.append(res)
        except Exception as e:
            log.error(f"Error evaluating {a.get('symbol')}: {e}")
    return results

def get_atom(atom_id: str) -> Dict:
    return ATOM_STORE.get(atom_id)
