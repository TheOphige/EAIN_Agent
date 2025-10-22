import os
import json
import time
from src.utils.helpers import sha256_of_obj, pretty_json
from src.utils.config import PROVENANCE_DIR
from src.utils.logger import log

os.makedirs(PROVENANCE_DIR, exist_ok=True)

def record_provenance_blob(raw_api_response: dict, tag: str = None) -> dict:
    """
    Save a provenance JSON containing:
      - original API response (raw_api_response)
      - a SHA256 hash of the sorted JSON
      - timestamp, source and optional tag
    Returns the provenance entry dict.
    """
    ts = int(time.time())
    hash_ = sha256_of_obj(raw_api_response)
    entry = {
        "timestamp": ts,
        "source": raw_api_response.get("source", "unknown"),
        "symbol": raw_api_response.get("symbol") or raw_api_response.get("id"),
        "hash": hash_,
        "raw": raw_api_response,
        "tag": tag
    }
    filename = f"{entry['symbol']}_{ts}.json"
    path = os.path.join(PROVENANCE_DIR, filename)
    try:
        with open(path, "w") as f:
            f.write(pretty_json(entry))
        log.info(f"[PROVENANCE] Wrote provenance for {entry['symbol']} -> {hash_}")
    except Exception as e:
        log.error(f"Failed to write provenance file {path}: {e}")
    return {"symbol": entry["symbol"], "hash": hash_, "path": path, "timestamp": ts}
