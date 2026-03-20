from fastapi import APIRouter

from app.services.portfolio_service import PortfolioService
from app.services.risk_service import RiskService


router = APIRouter()
risk_service = RiskService(PortfolioService())


@router.get("/report")
def get_risk_report():
    return risk_service.get_risk_report()


@router.post("/stress")
def run_stress_scenario(name: str = "SPX -10%"):
    return risk_service.run_stress_scenario(name)
