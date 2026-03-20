from pydantic import BaseModel


class PositionPnL(BaseModel):
    symbol: str
    market_value: float
    unrealized_pnl: float
    unrealized_return_pct: float
    contribution_pct: float


class PortfolioPnL(BaseModel):
    total_market_value: float
    total_unrealized_pnl: float
    positions: list[PositionPnL]
