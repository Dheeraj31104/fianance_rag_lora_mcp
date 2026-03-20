#!/usr/bin/env python3

from pathlib import Path


EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
GENERATION_MODEL_NAME = "distilgpt2"

OUTPUT_DIR = Path("./finance_lora")
ADAPTERS_DIR = Path("./finance_lora_adapters")
KNOWLEDGE_BASE_PATH = Path("finance_knowledge_base.json")

MAX_LENGTH = 128
CORPUS_LIMIT = 500

TEST_PROMPTS = [
    "What is a stock?",
    "How do bonds work?",
    "Explain portfolio diversification in one sentence.",
    "What is the risk of long-term government bonds?",
    "Why do companies pay dividends?",
    "How does inflation affect bond prices?",
]
