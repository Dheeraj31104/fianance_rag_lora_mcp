from app.models.summary import AnalysisSummary
from app.services.news_service import NewsService
from app.services.pnl_service import PnLService
from app.services.portfolio_service import PortfolioService
from app.services.rag_service import RAGService
from app.services.risk_service import RiskService


class SummaryService:
    def __init__(self):
        self.portfolio_service = PortfolioService()
        self.pnl_service = PnLService(self.portfolio_service)
        self.risk_service = RiskService(self.portfolio_service)
        self.news_service = NewsService()
        self.rag_service = RAGService()

    def build_portfolio_summary(self) -> AnalysisSummary:
        positions = self.portfolio_service.get_positions()
        events = []
        for position in positions[:2]:
            events.extend(self.news_service.get_stock_events(position.symbol)[:1])

        return AnalysisSummary(
            portfolio=self.portfolio_service.get_snapshot(),
            pnl=self.pnl_service.get_portfolio_pnl(),
            risk=self.risk_service.get_risk_report(),
            events=events,
            definitions=[
                self.rag_service.answer("What is portfolio diversification?"),
                self.rag_service.answer("What is market volatility?"),
            ],
        )
