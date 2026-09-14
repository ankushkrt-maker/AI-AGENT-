"""Compatibility wrapper for the V2 multi-provider market-data layer."""
from app.market.provider import klines, ticker_24h

__all__ = ["klines", "ticker_24h"]
