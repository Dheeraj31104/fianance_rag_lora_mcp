from pydantic import BaseModel


class StressScenarioResult(BaseModel):
    scenario: str
    estimated_pnl: float


class RiskReport(BaseModel):
    largest_position: str
    largest_sector: str
    concentration_pct: float
    stress_results: list[StressScenarioResult]
