from app.models.pnl import PortfolioPnL, PositionPnL
from app.services.portfolio_service import PortfolioService


class PnLService:
    def __init__(self, portfolio_service: PortfolioService):
        self.portfolio_service = portfolio_service

    def get_portfolio_pnl(self) -> PortfolioPnL:
        positions = self.portfolio_service.get_positions()
        total_market_value = sum(p.quantity * p.current_price for p in positions)

        pnl_rows = []
        for position in positions:
            market_value = position.quantity * position.current_price
            cost_basis = position.quantity * position.avg_cost
            unrealized_pnl = market_value - cost_basis
            contribution_pct = 0.0 if total_market_value == 0 else (market_value / total_market_value) * 100
            pnl_rows.append(
                PositionPnL(
                    symbol=position.symbol,
                    market_value=round(market_value, 2),
                    unrealized_pnl=round(unrealized_pnl, 2),
                    unrealized_return_pct=round((unrealized_pnl / cost_basis) * 100, 2),
                    contribution_pct=round(contribution_pct, 2),
                )
            )

        return PortfolioPnL(
            total_market_value=round(total_market_value, 2),
            total_unrealized_pnl=round(sum(item.unrealized_pnl for item in pnl_rows), 2),
            positions=pnl_rows,
        )
