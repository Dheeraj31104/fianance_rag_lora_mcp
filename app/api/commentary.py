from fastapi import APIRouter

from app.services.commentary_service import CommentaryService


router = APIRouter()
commentary_service = CommentaryService()


@router.post("/portfolio")
def generate_portfolio_commentary():
    return commentary_service.generate_portfolio_commentary()


@router.post("/stock/{symbol}")
def generate_stock_commentary(symbol: str):
    return commentary_service.generate_stock_commentary(symbol)
