from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat_service import ChatService


router = APIRouter()
chat_service = ChatService()


class ChatRequest(BaseModel):
    message: str
    symbol: str = "AAPL"


@router.post("")
def chat(request: ChatRequest):
    return chat_service.reply(request.message, request.symbol)
