class MarketDataService:
    """Replace these stubs with real market data adapters."""

    _prices = {
        "AAPL": {"price": 211.32, "change_pct": 1.2, "market_cap": 3200_000_000_000, "pe_ratio": 31.2, "beta": 1.1},
        "MSFT": {"price": 428.15, "change_pct": 0.8, "market_cap": 3100_000_000_000, "pe_ratio": 34.8, "beta": 0.9},
        "TSLA": {"price": 177.42, "change_pct": -2.3, "market_cap": 565_000_000_000, "pe_ratio": 62.5, "beta": 2.0},
    }
    _history = {
        "AAPL": [188.4, 191.8, 197.1, 202.6, 211.32],
        "MSFT": [401.2, 407.4, 412.5, 420.0, 428.15],
        "TSLA": [225.0, 214.0, 205.8, 191.4, 177.42],
    }

    def get_price(self, symbol: str) -> float:
        return self._prices[symbol.upper()]["price"]

    def get_stock_overview(self, symbol: str) -> dict:
        item = self._prices[symbol.upper()]
        return {
            "symbol": symbol.upper(),
            "price": item["price"],
            "change_pct": item["change_pct"],
            "market_cap": item["market_cap"],
            "pe_ratio": item["pe_ratio"],
            "beta": item["beta"],
        }

    def get_price_history(self, symbol: str) -> list[float]:
        return self._history[symbol.upper()]
