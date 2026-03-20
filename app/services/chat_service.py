from __future__ import annotations

from app.services.news_service import NewsService
from app.services.summary_service import SummaryService


class ChatService:
    """Context-aware dashboard chatbot built on deterministic analytics plus RAG."""

    def __init__(self):
        self.summary_service = SummaryService()
        self.news_service = NewsService()

    def reply(self, message: str, symbol: str = "AAPL") -> dict:
        summary = self.summary_service.build_portfolio_summary()
        text = message.strip()
        normalized = text.lower()
        symbol = symbol.upper()

        top_position = max(summary.pnl.positions, key=lambda item: item.contribution_pct)
        top_stress = summary.risk.stress_results[0]
        selected_events = self.news_service.get_stock_events(symbol)

        if any(term in normalized for term in ["why", "move", "moving", "today", "p&l"]):
            answer = (
                f"Portfolio P&L is {summary.portfolio.daily_pnl:,.2f} on NAV of {summary.portfolio.nav:,.2f}. "
                f"The largest position is {summary.risk.largest_position} and the biggest sector is {summary.risk.largest_sector}. "
                f"That means the portfolio is currently most sensitive to moves in those exposures. "
                f"Recent watch items include: {'; '.join(event.headline for event in summary.events)}."
            )
            citations = [
                f"Daily P&L: {summary.portfolio.daily_pnl:,.2f}",
                f"Largest position: {summary.risk.largest_position}",
                f"Largest sector: {summary.risk.largest_sector}",
            ]
        elif any(term in normalized for term in ["risk", "stress", "concentration"]):
            answer = (
                f"The current concentration is {summary.risk.concentration_pct:.2f}% in {summary.risk.largest_position}, "
                f"with {summary.risk.largest_sector} as the largest sector. "
                f"The top stress scenario is {top_stress.scenario} with estimated P&L of {top_stress.estimated_pnl:,.2f}. "
                f"This setup means single-name and sector concentration are the main portfolio risks."
            )
            citations = [
                f"Concentration: {summary.risk.concentration_pct:.2f}%",
                f"Top stress: {top_stress.scenario} -> {top_stress.estimated_pnl:,.2f}",
            ]
        elif symbol in normalized or any(term in normalized for term in ["stock", "event", "news", "aapl", "msft", "tsla"]):
            answer = (
                f"For {symbol}, the key event flow is: {'; '.join(event.headline for event in selected_events)}. "
                f"If you are analyzing this name in the portfolio, compare those events against its weight, unrealized P&L, and sector exposure."
            )
            citations = [event.headline for event in selected_events]
        else:
            concept_query = self._map_to_concept(normalized)
            concept = self.summary_service.rag_service.answer(concept_query)
            answer = (
                f"{concept['response']} "
                f"In this dashboard, that matters because {top_position.symbol} is the largest contributor by weight at "
                f"{top_position.contribution_pct:.2f}% and the portfolio's top sector is {summary.risk.largest_sector}."
            )
            citations = [
                f"Concept: {concept['matched_question']}",
                f"Top contributor: {top_position.symbol} at {top_position.contribution_pct:.2f}%",
            ]

        return {
            "message": text,
            "symbol": symbol,
            "answer": answer,
            "citations": citations,
        }

    def _map_to_concept(self, normalized_message: str) -> str:
        if "divers" in normalized_message or "concentration" in normalized_message:
            return "What is portfolio diversification?"
        if "volatility" in normalized_message:
            return "What is market volatility?"
        if "risk" in normalized_message:
            return "What is risk management in investing?"
        if "return" in normalized_message or "appreciation" in normalized_message:
            return "What is capital appreciation?"
        return "What is a stock?"
