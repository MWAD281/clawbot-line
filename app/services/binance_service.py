import logging

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://api.binance.com/api/v3"
_TIMEOUT = 8.0


async def get_price(symbol: str) -> dict:
    """Current best price for a trading pair."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(f"{_BASE}/ticker/price", params={"symbol": symbol.upper()})
        r.raise_for_status()
        return r.json()


async def get_24h_stats(symbol: str) -> dict:
    """24-hour rolling statistics: price change, high, low, volume."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(f"{_BASE}/ticker/24hr", params={"symbol": symbol.upper()})
        r.raise_for_status()
        data = r.json()
        return {
            "symbol": data["symbol"],
            "lastPrice": data["lastPrice"],
            "priceChange": data["priceChange"],
            "priceChangePercent": data["priceChangePercent"],
            "highPrice": data["highPrice"],
            "lowPrice": data["lowPrice"],
            "volume": data["volume"],
            "quoteVolume": data["quoteVolume"],
        }


async def get_klines(symbol: str, interval: str, limit: int = 24) -> list:
    """OHLCV candlestick data for technical analysis."""
    limit = min(limit, 100)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.get(
            f"{_BASE}/klines",
            params={"symbol": symbol.upper(), "interval": interval, "limit": limit},
        )
        r.raise_for_status()
        return [
            {
                "open_time_ms": k[0],
                "open": k[1],
                "high": k[2],
                "low": k[3],
                "close": k[4],
                "volume": k[5],
            }
            for k in r.json()
        ]
