from pydantic import BaseModel

from app.models.event import EventItem
from app.models.pnl import PortfolioPnL
from app.models.portfolio import PortfolioSnapshot
from app.models.risk import RiskReport


class AnalysisSummary(BaseModel):
    portfolio: PortfolioSnapshot
    pnl: PortfolioPnL
    risk: RiskReport
    events: list[EventItem]
    definitions: list[dict]
