import hashlib
import json
import time
from .logger import log

def sha256_of_obj(obj) -> str:
    """Return hex sha256 of JSON-serialised object (stable sort)."""
    raw = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def timestamp_secs():
    return int(time.time())

def safe_get(d, key, default=None):
    return d.get(key, default) if isinstance(d, dict) else default

def pretty_json(obj):
    return json.dumps(obj, indent=2, sort_keys=True, default=str)
