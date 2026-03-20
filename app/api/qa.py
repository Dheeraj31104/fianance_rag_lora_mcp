from fastapi import APIRouter

from app.services.rag_service import RAGService


router = APIRouter()
rag_service = RAGService()


@router.post("/explain")
def explain_term(query: str):
    return rag_service.answer(query)
