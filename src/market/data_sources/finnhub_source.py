import time
import requests
from src.utils.config import FINNHUB_API_KEY
from src.utils.logger import log
from src.utils.helpers import safe_get

BASE_URL = "https://finnhub.io/api/v1"

def _get(endpoint: str, params: dict):
    params = params or {}
    params.update({"token": FINNHUB_API_KEY})
    resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def fetch(symbol: str) -> dict:
    """Fetch live quote + profile + esg data for a symbol from Finnhub."""
    if not FINNHUB_API_KEY:
        log.error("FINNHUB_API_KEY is not set in environment")
        return None
    try:
        quote = _get("quote", {"symbol": symbol})
        profile = _get("stock/profile2", {"symbol": symbol})
        # esg may not exist for some symbols — handle gracefully
        try:
            esg = _get("stock/esg", {"symbol": symbol})
        except requests.HTTPError:
            esg = {}
        asset = {
            "symbol": symbol,
            "price": safe_get(quote, "c"),
            "open": safe_get(quote, "o"),
            "high": safe_get(quote, "h"),
            "low": safe_get(quote, "l"),
            "prev_close": safe_get(quote, "pc"),
            "change": safe_get(quote, "d"),
            "percent_change": safe_get(quote, "dp"),
            "timestamp": int(time.time()),
            "sector": safe_get(profile, "finnhubIndustry"),
            "market_cap": safe_get(profile, "marketCapitalization"),
            "name": safe_get(profile, "name"),
            "exchange": safe_get(profile, "exchange"),
            "currency": safe_get(profile, "currency"),
            # ESG fields — may be None
            "carbon_emissions": safe_get(esg, "carbonEmissions"),
            "total_emissions": safe_get(esg, "totalEmissions"),
            "governance_score": safe_get(esg, "governanceScore"),
            "sustainability_report": safe_get(esg, "sustainabilityReport"),
            "source": "finnhub"
        }
        return asset
    except requests.HTTPError as e:
        log.error(f"Finnhub HTTP error for {symbol}: {e}")
    except Exception as exc:
        log.error(f"Unexpected error fetching {symbol} from Finnhub: {exc}")
    return None
