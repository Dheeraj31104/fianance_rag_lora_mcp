from fastapi import APIRouter

from app.services.commentary_service import CommentaryService
from app.services.market_data_service import MarketDataService
from app.services.news_service import NewsService
from app.services.portfolio_service import PortfolioService


router = APIRouter()
market_data_service = MarketDataService()
news_service = NewsService()
commentary_service = CommentaryService()
portfolio_service = PortfolioService()


@router.get("/{symbol}/overview")
def get_stock_overview(symbol: str):
    return market_data_service.get_stock_overview(symbol)


@router.get("/{symbol}/events")
def get_stock_events(symbol: str):
    return news_service.get_stock_events(symbol)


@router.get("/{symbol}/drilldown")
def get_stock_drilldown(symbol: str):
    symbol = symbol.upper()
    positions = {position.symbol: position for position in portfolio_service.get_positions()}
    position = positions.get(symbol)
    return {
        "overview": market_data_service.get_stock_overview(symbol),
        "price_history": market_data_service.get_price_history(symbol),
        "events": news_service.get_stock_events(symbol),
        "commentary": commentary_service.generate_stock_commentary(symbol),
        "portfolio_position": {
            "quantity": position.quantity if position else 0,
            "avg_cost": position.avg_cost if position else 0,
            "current_price": position.current_price if position else 0,
            "sector": position.sector if position else "Unknown",
        },
    }
