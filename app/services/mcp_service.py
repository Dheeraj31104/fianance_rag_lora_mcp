from app.services.commentary_service import CommentaryService
from app.services.portfolio_service import PortfolioService
from app.services.rag_service import RAGService
from app.services.risk_service import RiskService


class MCPService:
    def __init__(self):
        portfolio_service = PortfolioService()
        self.portfolio_service = portfolio_service
        self.risk_service = RiskService(portfolio_service)
        self.rag_service = RAGService()
        self.commentary_service = CommentaryService()

    def get_tools(self) -> dict:
        return {
            "get_portfolio_snapshot": self.portfolio_service.get_snapshot,
            "get_positions": self.portfolio_service.get_positions,
            "get_risk_report": self.risk_service.get_risk_report,
            "answer_finance_question": self.rag_service.answer,
            "generate_portfolio_commentary": self.commentary_service.generate_portfolio_commentary,
        }
