"""
metta_shim.py

A minimal MeTTa-like shim for the hackathon:
- Accepts investor profile atoms and asset atoms (dicts)
- Runs a small set of rules (implemented as Python functions)
- Returns a Decision dict with:
    { asset, decision, score, reason_tree, confidence, provenance }
Designed to be simple, deterministic and explainable.
"""

from typing import Dict, List
from src.utils.logger import log
from src.utils.helpers import timestamp_secs, pretty_json
from src.provenance.provenance import record_provenance_blob

# Threshold presets for risk tolerance mapping
RISK_THRESHOLDS = {
    "low": {"max_volatility": 0.15, "min_return": 0.03},
    "medium": {"max_volatility": 0.30, "min_return": 0.06},
    "high": {"max_volatility": 0.60, "min_return": 0.12},
}

def _rule_exclude_industry(investor: Dict, asset: Dict) -> Dict:
    """Reject if asset sector is in investor's excluded industries."""
    excluded = investor.get("excluded_industries") or []
    sector = asset.get("sector", "") or ""
    if not excluded:
        return {"outcome": None}
    if sector.lower() in [s.strip().lower() for s in excluded]:
        return {
            "outcome": "reject",
            "rule": "exclude_by_industry",
            "evidence": {"sector": sector, "excluded": excluded},
            "confidence": 0.95,
            "note": f"Asset sector '{sector}' matches investor excluded industries"
        }
    return {"outcome": None}

def _rule_exclude_by_carbon(investor: Dict, asset: Dict) -> Dict:
    """Reject if carbon_emissions/carbon score > investor.max_carbon_score (if set)."""
    max_carbon = investor.get("max_carbon_score")
    asset_carbon = asset.get("carbon_emissions") or asset.get("carbon_score")
    if max_carbon is None or asset_carbon is None:
        return {"outcome": None}
    try:
        ac = float(asset_carbon)
    except Exception:
        return {"outcome": None}
    if ac > float(max_carbon):
        return {
            "outcome": "reject",
            "rule": "exclude_by_carbon",
            "evidence": {"carbon": ac, "max_allowed": max_carbon},
            "confidence": 0.9,
            "note": f"Asset carbon {ac} > investor max {max_carbon}"
        }
    return {"outcome": None}

def _rule_recent_large_drop(investor: Dict, asset: Dict) -> Dict:
    """Deprioritize if the percent change in last quote is less than -5%."""
    pct = asset.get("percent_change")
    if pct is None:
        return {"outcome": None}
    try:
        if float(pct) <= -5:
            return {
                "outcome": "deprioritize",
                "rule": "recent_large_drop",
                "evidence": {"percent_change": pct},
                "confidence": 0.7,
                "note": "Asset dropped more than 5% recently"
            }
    except Exception:
        pass
    return {"outcome": None}

def _rule_return_and_risk(investor: Dict, asset: Dict) -> Dict:
    """Accept if expected_return >= threshold & volatility <= threshold (simple heuristic).
       Use investor.goal and risk_tolerance to tune. For MVP we guess expected_return
       from analyst estimates or use percent_change as proxy if absent.
    """
    risk = investor.get("risk_tolerance", "medium")
    thresholds = RISK_THRESHOLDS.get(risk, RISK_THRESHOLDS["medium"])
    expected_return = asset.get("expected_return")
    volatility = asset.get("volatility") or asset.get("beta") or asset.get("stddev")

    # Fallback heuristics if expected_return missing: use percent_change as proxy
    if expected_return is None:
        pct = asset.get("percent_change")
        if pct is not None:
            expected_return = max(float(pct) / 100.0, 0.0)  # naive
    try:
        exp_r = float(expected_return) if expected_return is not None else None
    except Exception:
        exp_r = None
    try:
        vol = float(volatility) if volatility is not None else None
    except Exception:
        vol = None

    # If we can't compute, return no outcome but low confidence score
    if exp_r is None:
        return {"outcome": None}

    if exp_r >= thresholds["min_return"] and (vol is None or vol <= thresholds["max_volatility"]):
        return {
            "outcome": "accept",
            "rule": "accept_by_return_and_risk",
            "evidence": {"expected_return": exp_r, "volatility": vol, "thresholds": thresholds},
            "confidence": 0.8,
            "note": "Meets expected return and volatility thresholds"
        }
    else:
        return {
            "outcome": "deprioritize",
            "rule": "deprioritize_by_return_or_risk",
            "evidence": {"expected_return": exp_r, "volatility": vol, "thresholds": thresholds},
            "confidence": 0.6,
            "note": "Fails return / volatility requirements"
        }

# Ordered list of rule functions to execute (short-circuiting where appropriate)
RULES = [
    _rule_exclude_industry,
    _rule_exclude_by_carbon,
    _rule_recent_large_drop,
    _rule_return_and_risk
]

def evaluate_asset(investor: Dict, asset: Dict, record_provenance: bool = True) -> Dict:
    """
    Evaluate a single asset for an investor.
    Returns a Decision dict:
    {
        "asset": symbol,
        "decision": "accept" | "reject" | "deprioritize",
        "score": float,
        "reason_tree": [ {rule, evidence, note, confidence}, ... ],
        "confidence": float,
        "provenance": { hash/path/timestamp }
    }
    """
    symbol = asset.get("symbol") or asset.get("id") or "UNKNOWN"
    reason_tree = []
    final_decision = None
    final_confidence = 0.0

    # Run through rules in order; collect reason nodes
    for rule_fn in RULES:
        try:
            res = rule_fn(investor, asset)
        except Exception as e:
            log.error(f"Rule {rule_fn.__name__} exception for {symbol}: {e}")
            continue
        if not res or res.get("outcome") is None:
            continue
        # Append reason node
        node = {
            "rule": res.get("rule", rule_fn.__name__),
            "outcome": res.get("outcome"),
            "evidence": res.get("evidence"),
            "note": res.get("note"),
            "confidence": float(res.get("confidence", 0.5))
        }
        reason_tree.append(node)
        # Decide precedence: reject overrides accept. deprioritize is weaker than accept.
        if node["outcome"] == "reject":
            final_decision = "reject"
            final_confidence = max(final_confidence, node["confidence"])
            break  # immediate reject
        if node["outcome"] == "accept":
            # accept if not previously rejected
            if final_decision != "accept":
                final_decision = "accept"
                final_confidence = max(final_confidence, node["confidence"])
        if node["outcome"] == "deprioritize":
            if final_decision not in ("accept", "reject"):
                final_decision = "deprioritize"
                final_confidence = max(final_confidence, node["confidence"])

    # If no rule fired, default: deprioritize with low confidence
    if final_decision is None:
        final_decision = "deprioritize"
        final_confidence = 0.2
        reason_tree.append({
            "rule": "default_deprioritize",
            "outcome": "deprioritize",
            "evidence": None,
            "note": "No rules strongly matched; default deprioritize",
            "confidence": final_confidence
        })

    # Compute a naive score: map decision -> numeric, multiply by confidence
    mapping = {"accept": 1.0, "deprioritize": 0.5, "reject": 0.0}
    score = mapping.get(final_decision, 0.5) * final_confidence

    # Record provenance for the asset API response if asked
    provenance_entry = None
    if record_provenance:
        try:
            provenance_entry = record_provenance_blob(asset, tag="metta_input")
        except Exception as e:
            log.error(f"Failed to record provenance for {symbol}: {e}")

    decision = {
        "asset": symbol,
        "decision": final_decision,
        "score": score,
        "reason_tree": reason_tree,
        "confidence": final_confidence,
        "provenance": provenance_entry,
        "timestamp": timestamp_secs()
    }

    log.info(f"[METTA_SHIM] Decision for {symbol}: {final_decision} (score {score})")
    # Optionally log the full decision for debugging
    # log.debug(pretty_json(decision))

    return decision
