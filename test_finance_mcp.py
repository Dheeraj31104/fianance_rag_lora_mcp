#!/usr/bin/env python3

import json
from types import SimpleNamespace

import pandas as pd
import pytest

import finance_mcp_server as mcp


def test_list_tools_exposes_registered_tools():
    server = mcp.create_server()

    response = json.loads(server.handle_request(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})))

    tool_names = {tool["name"] for tool in response["result"]["tools"]}
    assert tool_names == {
        "get_stock_price",
        "scrape_finance_news",
        "calculate_investment",
        "answer_finance_question",
    }


def test_handle_request_returns_parse_error_for_invalid_json():
    server = mcp.create_server()

    response = json.loads(server.handle_request("{invalid json"))

    assert response["error"]["code"] == -32700


def test_call_tool_rejects_non_object_arguments():
    server = mcp.create_server()

    response = server.call_tool("calculate_investment", ["bad", "args"])

    assert response == {"error": "Tool arguments must be a JSON object"}


def test_call_tool_returns_invalid_argument_error():
    server = mcp.create_server()

    response = server.call_tool("calculate_investment", {"initial": 1000})

    assert "Invalid arguments" in response["error"]


def test_calculate_investment_standard_case():
    result = mcp.calculate_investment(initial=5000, annual_rate=8, years=10)

    assert result == {
        "initial": 5000,
        "rate_percent": 8,
        "years": 10,
        "final_amount": 10794.62,
        "total_gain": 5794.62,
        "total_return_percent": 115.89,
    }


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"initial": 0, "annual_rate": 5, "years": 3}, "Initial investment must be greater than 0"),
        ({"initial": 1000, "annual_rate": 5, "years": 0}, "Years must be greater than 0"),
    ],
)
def test_calculate_investment_rejects_invalid_input(payload, message):
    result = mcp.calculate_investment(**payload)

    assert result == {"error": message}


def test_get_stock_price_happy_path(monkeypatch):
    history = pd.DataFrame({"Close": [100.0, 104.25]})
    ticker = SimpleNamespace(
        history=lambda period: history,
        info={"fiftyTwoWeekHigh": 150.0, "fiftyTwoWeekLow": 80.0},
    )
    fake_yf = SimpleNamespace(Ticker=lambda symbol: ticker)

    monkeypatch.setitem(__import__("sys").modules, "yfinance", fake_yf)

    result = mcp.get_stock_price("aapl")

    assert result == {
        "symbol": "AAPL",
        "current_price": 104.25,
        "change": 4.25,
        "change_percent": 4.25,
        "52_week_high": 150.0,
        "52_week_low": 80.0,
    }


def test_get_stock_price_handles_single_close(monkeypatch):
    history = pd.DataFrame({"Close": [101.5]})
    ticker = SimpleNamespace(history=lambda period: history, info={})
    fake_yf = SimpleNamespace(Ticker=lambda symbol: ticker)

    monkeypatch.setitem(__import__("sys").modules, "yfinance", fake_yf)

    result = mcp.get_stock_price("msft")

    assert result["symbol"] == "MSFT"
    assert result["change"] == 0.0
    assert result["change_percent"] == 0.0


def test_get_stock_price_returns_error_for_empty_history(monkeypatch):
    history = pd.DataFrame({"Close": []})
    ticker = SimpleNamespace(history=lambda period: history, info={})
    fake_yf = SimpleNamespace(Ticker=lambda symbol: ticker)

    monkeypatch.setitem(__import__("sys").modules, "yfinance", fake_yf)

    result = mcp.get_stock_price("missing")

    assert result == {"error": "Stock 'MISSING' not found"}


def test_scrape_finance_news_happy_path(monkeypatch):
    html = """
    <html>
      <h1 class="firstHeading">Stock</h1>
      <div id="mw-content-text">
        <p>Stocks represent ownership in a company.</p>
        <p>Investors use them for growth and income.</p>
      </div>
    </html>
    """

    def fake_get(url, headers, timeout):
        return SimpleNamespace(status_code=200, content=html.encode("utf-8"))

    monkeypatch.setattr(mcp.requests, "get", fake_get)

    result = mcp.scrape_finance_news("Stock")

    assert result["topic"] == "Stock"
    assert result["url"].endswith("/Stock")
    assert "ownership in a company" in result["content"]
    assert result["length"] >= len(result["content"])


def test_scrape_finance_news_rejects_missing_content(monkeypatch):
    html = "<html><h1 class='firstHeading'>Stock</h1></html>"

    def fake_get(url, headers, timeout):
        return SimpleNamespace(status_code=200, content=html.encode("utf-8"))

    monkeypatch.setattr(mcp.requests, "get", fake_get)

    result = mcp.scrape_finance_news("Stock")

    assert result == {"error": "Could not locate article content"}


def test_scrape_finance_news_returns_not_found(monkeypatch):
    def fake_get(url, headers, timeout):
        return SimpleNamespace(status_code=404, content=b"")

    monkeypatch.setattr(mcp.requests, "get", fake_get)

    result = mcp.scrape_finance_news("NotARealFinanceTopic")

    assert result == {"error": "Topic 'NotARealFinanceTopic' not found"}


def test_answer_finance_question_uses_shared_rag(monkeypatch):
    fake_rag = SimpleNamespace(
        answer_question=lambda query: {
            "query": query,
            "matched_question": "What is a stock?",
            "response": "A stock is ownership in a company.",
        }
    )
    monkeypatch.setattr(mcp, "get_shared_rag", lambda: fake_rag)

    result = mcp.answer_finance_question("What is a stock?")

    assert result == {
        "query": "What is a stock?",
        "matched_question": "What is a stock?",
        "response": "A stock is ownership in a company.",
        "model": "tfidf_cosine_retriever",
        "source": "shared_rag",
    }
