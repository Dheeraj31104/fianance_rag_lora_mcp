#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from pathlib import Path

from finance_config import CORPUS_LIMIT, KNOWLEDGE_BASE_PATH


CURATED_QAS = [
    ("What is a stock?", "A stock is a share of ownership in a company, giving the holder a claim on assets and earnings."),
    ("What is a bond?", "A bond is a loan to an issuer that pays interest and returns principal at maturity."),
    ("What is a dividend?", "A dividend is a distribution of a company’s profits to shareholders."),
    ("What is portfolio diversification?", "Diversification spreads investments across assets to reduce risk from any single position."),
    ("What is risk management in investing?", "Risk management limits potential losses using controls like sizing, diversification, and hedging."),
    ("What is fixed income?", "Fixed income refers to investments that pay scheduled interest, such as government and corporate bonds."),
    ("What is capital appreciation?", "Capital appreciation is the increase in the value of an investment over time."),
    ("What is market volatility?", "Volatility measures how much prices fluctuate; higher volatility means larger swings up or down."),
    ("What is dividend investing?", "Dividend investing focuses on buying companies that pay regular dividends to shareholders."),
    ("What are government bonds?", "Government bonds are debt securities issued by a government to fund spending, backed by its taxing power."),
]


def clean_snippet(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\b[\d]{4,}\b", "", text)
    return text.strip()


def load_knowledge_documents(
    limit: int = CORPUS_LIMIT,
    kb_path: Path = KNOWLEDGE_BASE_PATH,
) -> list[dict]:
    if not kb_path.exists():
        return []
    with kb_path.open("r", encoding="utf-8") as handle:
        docs = json.load(handle)
    return docs[:limit]


def build_qa_pairs(
    limit: int = CORPUS_LIMIT,
    kb_path: Path = KNOWLEDGE_BASE_PATH,
) -> list[tuple[str, str]]:
    qa_pairs = list(CURATED_QAS)

    for doc in load_knowledge_documents(limit=limit, kb_path=kb_path):
        source = (doc.get("source") or "").lower()
        if not source or "wikipedia" in source or "finance_site" in source:
            continue

        title = (doc.get("title") or "this concept").strip()
        content = (doc.get("content") or "").strip()
        if not content:
            continue

        first_sentence = content.split(".")[0].strip()
        if len(first_sentence) < 30:
            first_sentence = content[:200].strip()

        snippet = clean_snippet(first_sentence)
        if len(snippet) < 30:
            continue

        qa_pairs.append((f"What is {title}?", snippet))

    seen: set[tuple[str, str]] = set()
    deduped: list[tuple[str, str]] = []
    for qa_pair in qa_pairs:
        if qa_pair not in seen:
            deduped.append(qa_pair)
            seen.add(qa_pair)
    return deduped[:limit]


def build_training_texts(
    limit: int = CORPUS_LIMIT,
    kb_path: Path = KNOWLEDGE_BASE_PATH,
) -> list[str]:
    return [f"Question: {question}\nAnswer: {answer}" for question, answer in build_qa_pairs(limit=limit, kb_path=kb_path)]
