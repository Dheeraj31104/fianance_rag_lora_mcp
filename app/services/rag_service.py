from finance_rag import build_rag


class RAGService:
    def __init__(self):
        self.rag = build_rag()

    def answer(self, query: str) -> dict:
        result = self.rag.answer_question(query)
        result["source"] = "rag_service"
        return result
