#!/usr/bin/env python3
"""
MCP Server with Finance Tools
Run: python finance_mcp_server.py
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from finance_rag import RETRIEVER_NAME, build_rag


@dataclass(frozen=True)
class RegisteredTool:
    function: Callable[..., dict[str, Any]]
    description: str
    input_schema: dict[str, Any]


class FinanceMCPServer:
    """Minimal JSON-RPC server for finance tools."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: dict[str, RegisteredTool] = {}

    def register_tool(
        self,
        func: Callable[..., dict[str, Any]],
        description: str,
        input_schema: dict[str, Any],
    ) -> None:
        self.tools[func.__name__] = RegisteredTool(
            function=func,
            description=description,
            input_schema=input_schema,
        )

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for name, tool in self.tools.items()
        ]

    def call_tool(self, tool_name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
        tool = self.tools.get(tool_name)
        if tool is None:
            return {"error": f"Unknown tool: {tool_name}"}
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            return {"error": "Tool arguments must be a JSON object"}

        try:
            return tool.function(**arguments)
        except TypeError as exc:
            return {"error": f"Invalid arguments for '{tool_name}': {exc}"}
        except Exception as exc:  # pragma: no cover
            return {"error": f"Tool error: {exc}"}

    def handle_request(self, request_str: str) -> str:
        try:
            request = json.loads(request_str)
        except json.JSONDecodeError:
            return json.dumps(
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}
            )

        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if not isinstance(params, dict):
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": "Invalid params"},
                }
            )

        response: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}

        if method == "initialize":
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": self.name, "version": self.version},
            }
        elif method == "tools/list":
            response["result"] = {"tools": self.list_tools()}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            response["result"] = self.call_tool(tool_name, arguments)
        else:
            response["error"] = {"code": -32601, "message": "Method not found"}

        return json.dumps(response)

    def run(self) -> None:
        sys.stderr.write(f"\n{'=' * 70}\n")
        sys.stderr.write("  MCP SERVER: Finance Tools\n")
        sys.stderr.write(f"{'=' * 70}\n\n")
        sys.stderr.write("Available Tools:\n")
        sys.stderr.write("  1. get_stock_price(symbol) - Real stock prices\n")
        sys.stderr.write("  2. scrape_finance_news(topic) - Finance topic lookup\n")
        sys.stderr.write("  3. calculate_investment(initial, annual_rate, years) - Investment math\n")
        sys.stderr.write("  4. answer_finance_question(query) - Shared RAG answer\n\n")
        sys.stderr.write("Starting MCP server...\n")
        sys.stderr.write(f"{'-' * 70}\n\n")
        sys.stderr.flush()

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                sys.stdout.write(self.handle_request(line) + "\n")
                sys.stdout.flush()
        except KeyboardInterrupt:
            pass


def get_stock_price(symbol: str) -> dict[str, Any]:
    """Get recent stock pricing data from Yahoo Finance."""
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        return {"error": "Symbol is required"}

    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed"}

    try:
        stock = yf.Ticker(normalized_symbol)
        hist = stock.history(period="5d")
        if hist.empty:
            return {"error": f"Stock '{normalized_symbol}' not found"}

        closes = hist["Close"].dropna()
        if closes.empty:
            return {"error": f"No closing price data available for '{normalized_symbol}'"}

        current_price = float(closes.iloc[-1])
        previous_price = float(closes.iloc[-2]) if len(closes) > 1 else current_price
        change = current_price - previous_price
        change_percent = 0.0 if previous_price == 0 else (change / previous_price) * 100

        info = stock.info or {}
        result = {
            "symbol": normalized_symbol,
            "current_price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
        }

        fifty_two_week_high = info.get("fiftyTwoWeekHigh")
        fifty_two_week_low = info.get("fiftyTwoWeekLow")
        if fifty_two_week_high is not None:
            result["52_week_high"] = round(float(fifty_two_week_high), 2)
        if fifty_two_week_low is not None:
            result["52_week_low"] = round(float(fifty_two_week_low), 2)

        return result
    except Exception as exc:
        return {"error": str(exc)}


def scrape_finance_news(topic: str) -> dict[str, Any]:
    """Fetch a short finance topic summary from Wikipedia."""
    normalized_topic = topic.strip()
    if not normalized_topic:
        return {"error": "Topic is required"}

    url = f"https://en.wikipedia.org/wiki/{quote(normalized_topic.replace(' ', '_'))}"
    headers = {
        "User-Agent": "FinanceMCPServer/1.0 (+https://en.wikipedia.org/wiki/Main_Page)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as exc:
        return {"error": f"Request failed: {exc}"}

    if response.status_code == 404:
        return {"error": f"Topic '{normalized_topic}' not found"}
    if response.status_code != 200:
        return {"error": f"Wikipedia request failed with status {response.status_code}"}

    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.find("h1", class_="firstHeading")
    content_div = soup.find("div", id="mw-content-text")
    if content_div is None:
        return {"error": "Could not locate article content"}

    paragraphs = [
        paragraph.get_text(" ", strip=True)
        for paragraph in content_div.find_all("p")
        if paragraph.get_text(strip=True)
    ]
    if not paragraphs:
        return {"error": f"No article content found for '{normalized_topic}'"}

    content = " ".join(paragraphs[:3])
    content = " ".join(content.split())

    return {
        "topic": title.get_text(strip=True) if title else normalized_topic,
        "url": url,
        "content": content[:500],
        "length": len(content),
    }


def calculate_investment(initial: float, annual_rate: float, years: int) -> dict[str, Any]:
    """Calculate annual compounding for an investment."""
    if initial <= 0:
        return {"error": "Initial investment must be greater than 0"}
    if years <= 0:
        return {"error": "Years must be greater than 0"}

    rate_decimal = annual_rate / 100
    final_amount = initial * ((1 + rate_decimal) ** years)
    total_gain = final_amount - initial

    return {
        "initial": initial,
        "rate_percent": annual_rate,
        "years": years,
        "final_amount": round(final_amount, 2),
        "total_gain": round(total_gain, 2),
        "total_return_percent": round((total_gain / initial) * 100, 2),
    }


@lru_cache(maxsize=1)
def get_shared_rag():
    return build_rag()


def answer_finance_question(query: str) -> dict[str, Any]:
    """Answer a finance question using the shared RAG pipeline."""
    normalized_query = query.strip()
    if not normalized_query:
        return {"error": "Query is required"}

    try:
        result = get_shared_rag().answer_question(normalized_query)
        result["model"] = RETRIEVER_NAME
        result["source"] = "shared_rag"
        return result
    except Exception as exc:
        return {"error": f"RAG answer failed: {exc}"}


def create_server() -> FinanceMCPServer:
    server = FinanceMCPServer("Finance MCP Server")
    server.register_tool(
        get_stock_price,
        "Get recent stock price data",
        {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
    )
    server.register_tool(
        scrape_finance_news,
        "Fetch a short finance topic summary from Wikipedia",
        {
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": ["topic"],
        },
    )
    server.register_tool(
        calculate_investment,
        "Calculate investment returns",
        {
            "type": "object",
            "properties": {
                "initial": {"type": "number"},
                "annual_rate": {"type": "number"},
                "years": {"type": "integer"},
            },
            "required": ["initial", "annual_rate", "years"],
        },
    )
    server.register_tool(
        answer_finance_question,
        "Answer a finance question using the shared RAG pipeline",
        {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    )
    return server


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
