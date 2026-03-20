from app.models.portfolio import PortfolioSnapshot, Position
from app.services.market_data_service import MarketDataService


class PortfolioService:
    def __init__(self):
        self.market_data = MarketDataService()
        self._positions = [
            {"symbol": "AAPL", "quantity": 120, "avg_cost": 180.0, "sector": "Technology"},
            {"symbol": "MSFT", "quantity": 60, "avg_cost": 390.0, "sector": "Technology"},
            {"symbol": "TSLA", "quantity": 90, "avg_cost": 210.0, "sector": "Consumer Discretionary"},
        ]

    def get_positions(self) -> list[Position]:
        return [
            Position(
                symbol=item["symbol"],
                quantity=item["quantity"],
                avg_cost=item["avg_cost"],
                current_price=self.market_data.get_price(item["symbol"]),
                sector=item["sector"],
            )
            for item in self._positions
        ]

    def get_snapshot(self) -> PortfolioSnapshot:
        positions = self.get_positions()
        nav = sum(p.quantity * p.current_price for p in positions) + 125000.0
        daily_pnl = 5420.0
        return PortfolioSnapshot(
            nav=round(nav, 2),
            cash=125000.0,
            daily_pnl=daily_pnl,
            daily_return_pct=round((daily_pnl / nav) * 100, 2),
        )

    def get_sector_allocation(self) -> list[dict]:
        positions = self.get_positions()
        total_market_value = sum(p.quantity * p.current_price for p in positions)
        sector_totals: dict[str, float] = {}
        for position in positions:
            sector_totals[position.sector] = sector_totals.get(position.sector, 0.0) + (position.quantity * position.current_price)
        return [
            {
                "sector": sector,
                "market_value": round(value, 2),
                "weight_pct": round((value / total_market_value) * 100, 2) if total_market_value else 0.0,
            }
            for sector, value in sorted(sector_totals.items(), key=lambda item: item[1], reverse=True)
        ]
