#!/usr/bin/env python3
"""
Compare RAG vs LoRA vs MCP on a shared set of finance questions.

Run:
  python finance_compare.py
  python finance_compare.py --questions "What is a stock?" "How do bonds work?"
  python finance_compare.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

from finance_config import ADAPTERS_DIR, GENERATION_MODEL_NAME, TEST_PROMPTS


os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare RAG, LoRA, and MCP answers on shared prompts.")
    parser.add_argument("--questions", nargs="*", help="Optional custom questions to compare.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text report.")
    return parser.parse_args()


def timed_call(label: str, func, *args, **kwargs) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "method": label,
            "ok": "error" not in result if isinstance(result, dict) else True,
            "elapsed_ms": round(elapsed_ms, 2),
            "result": result,
        }
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "method": label,
            "ok": False,
            "elapsed_ms": round(elapsed_ms, 2),
            "result": {"error": str(exc)},
        }


def load_lora_runtime() -> dict[str, Any]:
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM

        from finance_lora import load_tokenizer
    except Exception as exc:
        return {"available": False, "reason": f"LoRA runtime import failed: {exc}"}

    if not Path(ADAPTERS_DIR).exists():
        return {"available": False, "reason": f"LoRA adapters not found at {ADAPTERS_DIR}"}

    tokenizer = load_tokenizer()
    base_model = AutoModelForCausalLM.from_pretrained(
        GENERATION_MODEL_NAME,
        local_files_only=True,
    )
    model = PeftModel.from_pretrained(base_model, ADAPTERS_DIR)
    model.eval()
    device = torch.device("cpu")
    model.to(device)
    return {
        "available": True,
        "tokenizer": tokenizer,
        "model": model,
        "device": device,
    }


def ask_lora(runtime: dict[str, Any], question: str) -> dict[str, Any]:
    from finance_lora import generate_answer

    if not runtime["available"]:
        return {"error": runtime["reason"]}
    answer = generate_answer(
        runtime["model"],
        runtime["tokenizer"],
        question,
        runtime["device"],
    )
    return {
        "query": question,
        "response": answer,
        "model": GENERATION_MODEL_NAME,
        "source": "lora_adapter",
    }


def compare_questions(questions: list[str]) -> list[dict[str, Any]]:
    from finance_mcp_server import create_server
    from finance_rag import build_rag

    rag = build_rag()
    server = create_server()
    lora_runtime = load_lora_runtime()

    comparisons: list[dict[str, Any]] = []
    for question in questions:
        rag_result = timed_call("rag", rag.answer_question, question)
        lora_result = timed_call("lora", ask_lora, lora_runtime, question)
        mcp_result = timed_call(
            "mcp",
            server.call_tool,
            "answer_finance_question",
            {"query": question},
        )
        comparisons.append(
            {
                "question": question,
                "results": [rag_result, lora_result, mcp_result],
            }
        )
    return comparisons


def print_text_report(comparisons: list[dict[str, Any]]) -> None:
    print("=" * 70)
    print("FINANCE MODEL COMPARISON")
    print("=" * 70)

    for comparison in comparisons:
        print(f"\nQ: {comparison['question']}")
        print("-" * 70)
        for item in comparison["results"]:
            result = item["result"]
            status = "OK" if item["ok"] else "ERROR"
            print(f"{item['method'].upper():<6} | {status:<5} | {item['elapsed_ms']:>8.2f} ms")
            if isinstance(result, dict) and "error" in result:
                print(f"Answer: ERROR: {result['error']}")
                continue

            answer = result.get("response") or result.get("content") or str(result)
            print(f"Answer: {answer}")
            if "matched_question" in result:
                print(f"Match : {result['matched_question']}")
            if "model" in result:
                print(f"Model : {result['model']}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Question':<34} {'RAG ms':>10} {'LoRA ms':>10} {'MCP ms':>10}")
    for comparison in comparisons:
        by_method = {item["method"]: item for item in comparison["results"]}
        print(
            f"{comparison['question'][:34]:<34} "
            f"{by_method['rag']['elapsed_ms']:>10.2f} "
            f"{by_method['lora']['elapsed_ms']:>10.2f} "
            f"{by_method['mcp']['elapsed_ms']:>10.2f}"
        )


def main() -> None:
    args = parse_args()
    questions = args.questions or TEST_PROMPTS
    comparisons = compare_questions(questions)

    if args.json:
        print(json.dumps(comparisons, indent=2))
        return

    print_text_report(comparisons)


if __name__ == "__main__":
    main()
