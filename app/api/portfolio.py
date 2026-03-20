from fastapi import APIRouter

from app.services.portfolio_service import PortfolioService
from app.services.pnl_service import PnLService


router = APIRouter()
portfolio_service = PortfolioService()
pnl_service = PnLService(portfolio_service)


@router.get("/snapshot")
def get_portfolio_snapshot():
    return portfolio_service.get_snapshot()


@router.get("/positions")
def get_positions():
    return portfolio_service.get_positions()


@router.get("/pnl")
def get_portfolio_pnl():
    return pnl_service.get_portfolio_pnl()


@router.get("/allocation")
def get_portfolio_allocation():
    return portfolio_service.get_sector_allocation()
