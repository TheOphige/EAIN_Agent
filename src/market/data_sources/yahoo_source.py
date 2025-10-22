"""
Placeholder Yahoo data source.

This file provides the same fetch(symbol) interface as finnhub_source.fetch,
so MarketAgent can easily switch or aggregate data later.

For MVP we keep this as a placeholder that uses yfinance as needed.
"""
import yfinance as yf
from src.utils.logger import log
from src.utils.helpers import safe_get
import time

def fetch(symbol: str) -> dict:
    try:
        t = yf.Ticker(symbol)
        info = t.info
        quote = t.history(period="1d")
        latest = None
        if not quote.empty:
            latest = quote.iloc[-1]
        asset = {
            "symbol": symbol,
            "price": float(latest["Close"]) if latest is not None else safe_get(info, "previousClose"),
            "timestamp": int(time.time()),
            "sector": safe_get(info, "sector"),
            "market_cap": safe_get(info, "marketCap"),
            "name": safe_get(info, "shortName"),
            "source": "yahoo"
        }
        return asset
    except Exception as e:
        log.error(f"Yahoo fetch error for {symbol}: {e}")
        return None
