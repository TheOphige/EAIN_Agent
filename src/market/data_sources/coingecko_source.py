from pycoingecko import CoinGeckoAPI
from src.utils.logger import log
import time

cg = CoinGeckoAPI()

def fetch(symbol_or_id: str) -> dict:
    """
    Fetch crypto asset by CoinGecko id (not ticker symbol).
    Example id: 'bitcoin', 'ethereum'
    """
    try:
        data = cg.get_price(ids=symbol_or_id, vs_currencies='usd', include_market_cap='true', include_24hr_vol='true', include_24hr_change='true')
        if not data or symbol_or_id not in data:
            return None
        entry = data[symbol_or_id]
        asset = {
            "symbol": symbol_or_id,
            "price": entry.get("usd"),
            "market_cap": entry.get("usd_market_cap"),
            "24h_change": entry.get("usd_24h_change"),
            "timestamp": int(time.time()),
            "source": "coingecko"
        }
        return asset
    except Exception as e:
        log.error(f"CoinGecko fetch error for {symbol_or_id}: {e}")
        return None
