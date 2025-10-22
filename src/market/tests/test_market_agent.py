import pytest
from src.market.market_agent import get_candidates

def test_get_candidates():
    # This test will use the live Finnhub API key; for CI mock it if needed.
    candidates = get_candidates(["AAPL", "MSFT"])
    assert isinstance(candidates, list)
    assert all("symbol" in c for c in candidates)
