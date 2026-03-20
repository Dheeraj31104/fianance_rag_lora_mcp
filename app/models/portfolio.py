from pydantic import BaseModel


class Position(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    sector: str


class PortfolioSnapshot(BaseModel):
    nav: float
    cash: float
    daily_pnl: float
    daily_return_pct: float
