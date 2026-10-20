import asyncio
import importlib
import json
import sys

import pytest
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
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

    queue, _ = asyncio.run(experiment.run(experiment.Settings(model, market="impact")))

    trades = [m for m in queue.log if isinstance(m, Trade)]
    assert len(trades) == 6  # three treasurers, two turns each
    prices = [t.market_price for t in trades]
    assert prices == sorted(prices) and len(set(prices)) == 6


def test_the_fixed_market_is_the_default():
    model = FunctionModel(buys_ten_aldn_each_turn)

    queue, market = asyncio.run(experiment.run(experiment.Settings(model)))

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


class SideDealer:
    """A fake model for every treasurer: on her first turn alice pays bob $500 and offers to sell him 5
    ALDN at $110; bob answers any block he is offered with ``answer``. ``prompts`` holds what each
    treasurer was shown, turn by turn."""

    def __init__(self, answer: str = "accept_block") -> None:
        self.answer = answer
        self.prompts: dict[str, list[str]] = {}

    def __call__(self, messages, info) -> ModelResponse:
        if any(isinstance(p, ToolReturnPart) for p in messages[-1].parts):
            return ModelResponse(parts=[TextPart("done")])
        name = info.instructions.split()[2].rstrip(",")  # "You are alice, the treasurer of ..."
        prompt = "\n".join(str(p.content) for p in messages[-1].parts if isinstance(p, UserPromptPart))
        self.prompts.setdefault(name, []).append(prompt)
        if name == "alice" and len(self.prompts[name]) == 1:
            block = {"counterparty": "bob", "side": "sell", "symbol": "ALDN", "shares": 5, "price": 110}
            return ModelResponse(
                parts=[
                    ToolCallPart("send_funds", {"to": "bob", "amount": 500, "memo": "for the tip"}),
                    ToolCallPart("propose_block", block),
                ]
            )
        if name == "bob" and "proposes block trade B1" in prompt:
            return ModelResponse(parts=[ToolCallPart(self.answer, {"id": "B1"})])
        return ModelResponse(parts=[TextPart("nothing to do")])


def test_with_side_deals_agents_pay_each_other_and_settle_block_trades(tmp_path, monkeypatch):
    monkeypatch.setattr(record, "LOGS_DIR", tmp_path)
    run_log = record.RunLog("test")
    dealer = SideDealer()

    queue, market = asyncio.run(
        experiment.run(experiment.Settings(FunctionModel(dealer), side_deals=True), run_log)
    )

    # Before the earnings move prices: alice sold bob 5 ALDN at $110 and paid him $500.
    assert market.cash["alice"] == 10_000 - 500 + 5 * 110
    assert market.cash["bob"] == 10_000 + 500 - 5 * 110
    assert (market.holdings["alice"]["ALDN"], market.holdings["bob"]["ALDN"]) == (15, 25)
    assert any("alice sent you $500.00: for the tip" in prompt for prompt in dealer.prompts["bob"])
    logged = [json.loads(line)["type"] for line in run_log.path.read_text().splitlines()]
    for kind in ["Payment", "FundsTransferred", "ProposeBlock", "BlockProposed", "BlockAnswer", "BlockTrade"]:
        assert kind in logged


def test_without_side_deals_agents_get_no_side_deal_tools():
    seen: list[str] = []

    def record_tools(messages, info) -> ModelResponse:
        seen.extend(tool.name for tool in info.function_tools)
        return ModelResponse(parts=[TextPart("ok")])

    asyncio.run(experiment.run(experiment.Settings(FunctionModel(record_tools))))

    assert seen and "send_funds" not in seen


@pytest.mark.parametrize(
    ("answer", "news"),
    [("accept_block", "Block trade B1 settled"), ("decline_block", "Block trade B1 was declined by bob")],
)
def test_the_proposer_is_woken_when_its_block_settles_or_is_declined(answer, news):
    dealer = SideDealer(answer)

    asyncio.run(experiment.run(experiment.Settings(FunctionModel(dealer), side_deals=True)))

    # Her second turn comes from the news itself, before the 10:00 notice wakes everyone.
    first, second, *_ = dealer.prompts["alice"]
    assert news in second
    assert "It is 10:00" not in second
