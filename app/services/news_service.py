from app.models.event import EventItem


class NewsService:
    def get_stock_events(self, symbol: str) -> list[EventItem]:
        symbol = symbol.upper()
        mock_news = {
            "AAPL": [
                EventItem(symbol="AAPL", headline="Services revenue remains resilient", category="earnings"),
                EventItem(symbol="AAPL", headline="Supply chain commentary points to stable demand", category="operations"),
            ],
            "MSFT": [
                EventItem(symbol="MSFT", headline="Cloud growth remains in focus", category="earnings"),
            ],
            "TSLA": [
                EventItem(symbol="TSLA", headline="Vehicle deliveries miss market expectations", category="sales"),
            ],
        }
        return mock_news.get(symbol, [EventItem(symbol=symbol, headline="No recent major event in stub feed", category="info")])
