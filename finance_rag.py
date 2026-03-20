#!/usr/bin/env python3
"""
RAG Pipeline with Finance Data
Run: python finance_rag.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from finance_knowledge import build_qa_pairs


RETRIEVER_NAME = "tfidf_cosine_retriever"


@dataclass
class FinanceRAG:
    vectorizer: TfidfVectorizer
    question_matrix: Any
    questions: list[str]
    answers: list[str]

    def answer_question(self, query: str) -> dict[str, Any]:
        query_vector = self.vectorizer.transform([query])
        scores = (self.question_matrix @ query_vector.T).toarray().ravel()
        top_idx = int(np.argmax(scores))
        return {
            "query": query,
            "matched_question": self.questions[top_idx],
            "response": self.answers[top_idx],
            "score": round(float(scores[top_idx]), 4),
        }


def build_rag() -> FinanceRAG:
    qa_pairs = build_qa_pairs()
    questions = [question for question, _ in qa_pairs]
    answers = [answer for _, answer in qa_pairs]

    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), stop_words="english")
    question_matrix = vectorizer.fit_transform(questions)

    return FinanceRAG(
        vectorizer=vectorizer,
        question_matrix=question_matrix,
        questions=questions,
        answers=answers,
    )


def main() -> None:
    print("=" * 70)
    print("TASK 1: RAG PIPELINE WITH FINANCE DATA")
    print("=" * 70)

    print("\n1. Preparing shared finance QAs...")
    qa_pairs = build_qa_pairs()
    print(f"   \u2713 Loaded {len(qa_pairs)} shared finance QA pairs")

    print("\n2. Building TF-IDF retriever...")
    rag = build_rag()
    print(f"   \u2713 Indexed {len(rag.questions)} questions")

    print("\n3. Testing RAG with finance questions...")
    for question in [
        "What is a stock?",
        "What are bonds?",
        "What is dividend investing?",
    ]:
        print(f"\n   Q: {question}")
        result = rag.answer_question(question)
        print(f"   Match: {result['matched_question']} ({result['score']})")
        print(f"   A: {result['response']}")


if __name__ == "__main__":
    main()
