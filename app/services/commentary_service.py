from app.services.news_service import NewsService
from app.services.summary_service import SummaryService


class CommentaryService:
    """Replace template commentary with LoRA or another LLM in production."""

    def __init__(self):
        self.summary_service = SummaryService()
        self.news_service = NewsService()

    def generate_portfolio_commentary(self) -> dict:
        summary = self.summary_service.build_portfolio_summary()
        top_position = max(summary.pnl.positions, key=lambda item: item.contribution_pct)
        return {
            "summary": (
                f"Portfolio NAV is {summary.portfolio.nav:,.2f} with daily P&L of "
                f"{summary.portfolio.daily_pnl:,.2f}. Largest exposure remains {summary.risk.largest_position}, "
                f"and the largest sector is {summary.risk.largest_sector}."
            ),
            "drivers": [
                f"{top_position.symbol} is the largest contributor by weight at {top_position.contribution_pct}%.",
                f"Top stress case {summary.risk.stress_results[0].scenario} implies {summary.risk.stress_results[0].estimated_pnl:,.2f}.",
            ],
            "watch_items": [event.headline for event in summary.events],
            "definitions": summary.definitions,
        }

    def generate_stock_commentary(self, symbol: str) -> dict:
        events = self.news_service.get_stock_events(symbol)
        return {
            "symbol": symbol.upper(),
            "summary": f"{symbol.upper()} should be reviewed alongside its latest event flow and current portfolio contribution.",
            "watch_items": [event.headline for event in events],
        }
