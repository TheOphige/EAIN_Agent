"""
MarketAgent abstraction that fetches asset data from configured sources.
This is not a full uAgent; rather a data provider the EAIN agent will call.
"""
from src.market.data_sources import finnhub_source, yahoo_source, coingecko_source
from src.utils.logger import log
from typing import List

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA"]

def get_asset_data(symbol: str, source: str = "finnhub") -> dict:
    if source == "finnhub":
        return finnhub_source.fetch(symbol)
    if source == "yahoo":
        return yahoo_source.fetch(symbol)
    if source == "coingecko":
        return coingecko_source.fetch(symbol)  # expects coingecko id
    log.error(f"Unsupported market data source requested: {source}")
    return None

def get_candidates(symbols: List[str] = None, source: str = "finnhub") -> List[dict]:
    symbols = symbols or DEFAULT_SYMBOLS
    results = []
    for sym in symbols:
        try:
            data = get_asset_data(sym, source=source)
            if data:
                results.append(data)
        except Exception as e:
            log.error(f"Error getting asset data for {sym}: {e}")
    return results
