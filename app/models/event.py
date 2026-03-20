from pydantic import BaseModel


class EventItem(BaseModel):
    symbol: str
    headline: str
    category: str
