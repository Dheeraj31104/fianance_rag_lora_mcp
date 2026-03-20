from collections import defaultdict

from app.models.risk import RiskReport, StressScenarioResult
from app.services.portfolio_service import PortfolioService


class RiskService:
    def __init__(self, portfolio_service: PortfolioService):
        self.portfolio_service = portfolio_service

    def get_risk_report(self) -> RiskReport:
        positions = self.portfolio_service.get_positions()
        market_values = {p.symbol: p.quantity * p.current_price for p in positions}
        total_market_value = sum(market_values.values())
        largest_position = max(market_values, key=market_values.get)

        sector_totals = defaultdict(float)
        for position in positions:
            sector_totals[position.sector] += position.quantity * position.current_price
        largest_sector = max(sector_totals, key=sector_totals.get)
        concentration_pct = (market_values[largest_position] / total_market_value) * 100

        return RiskReport(
            largest_position=largest_position,
            largest_sector=largest_sector,
            concentration_pct=round(concentration_pct, 2),
            stress_results=[
                StressScenarioResult(scenario="SPX -10%", estimated_pnl=-18250.0),
                StressScenarioResult(scenario="Rates +100bp", estimated_pnl=-6400.0),
            ],
        )

    def run_stress_scenario(self, scenario_name: str) -> StressScenarioResult:
        lookup = {
            "SPX -10%": -18250.0,
            "Rates +100bp": -6400.0,
            "Tech -15%": -22300.0,
        }
        return StressScenarioResult(
            scenario=scenario_name,
            estimated_pnl=lookup.get(scenario_name, -5000.0),
        )
