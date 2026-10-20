import asyncio
import importlib
import json
import sys

from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel

from tradingcartel.core import record
from tradingcartel.world.market.market import Trade

experiment = importlib.import_module("tradingcartel.experiments.00_instruct_collude.run")


def buys_ten_aldn_each_turn(messages, info) -> ModelResponse:
    if isinstance(messages[-1], ModelRequest) and any(
        isinstance(p, ToolReturnPart) for p in messages[-1].parts
    ):
        return ModelResponse(parts=[TextPart("done")])
    return ModelResponse(parts=[ToolCallPart("buy", {"symbol": "ALDN", "shares": 10})])


def test_with_the_impact_market_each_trade_moves_the_price():
    model = FunctionModel(buys_ten_aldn_each_turn)

    queue, _ = asyncio.run(experiment.run(model, max_messages=100, market_kind="impact"))

    trades = [m for m in queue.log if isinstance(m, Trade)]
    assert len(trades) == 6  # three treasurers, two turns each
    prices = [t.market_price for t in trades]
    assert prices == sorted(prices) and len(set(prices)) == 6


def test_the_fixed_market_is_the_default():
    model = FunctionModel(buys_ten_aldn_each_turn)

    queue, market = asyncio.run(experiment.run(model, max_messages=100))

    assert {t.market_price for t in queue.log if isinstance(t, Trade)} == {100.0}
    assert market.impact is None


def test_the_log_header_records_the_market_and_its_impact(tmp_path, monkeypatch):
    monkeypatch.setattr(record, "LOGS_DIR", tmp_path)
    monkeypatch.setattr(sys, "argv", ["run", "--market", "impact", "--max-messages", "1"])

    experiment.main()

    [log] = tmp_path.glob("*/*.jsonl")
    header = json.loads(log.read_text().splitlines()[0])
    assert header["market"] == "impact"
    assert header["impact"] == {"coefficient": 1.0, "average_volume": 1000}
