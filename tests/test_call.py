"""The Codex caller, with a fake codex: the locked-down command, the reply read off its events, and what the
call lets codex see. No test calls a model."""

import json
import subprocess
from pathlib import Path

import pytest

from zerocommcartel import call
from zerocommcartel.call import MODELS, PAID_OK, CallFailed, codex_command, codex_reply, openrouter_body


def events(*items, usage=None):
    """`codex exec --json` output for one turn whose completed items are `items`."""
    lines: list[dict] = [{"type": "thread.started", "thread_id": "t"}, {"type": "turn.started"}]
    lines += [{"type": "item.completed", "item": item} for item in items]
    lines.append({"type": "turn.completed", "usage": usage or {"input_tokens": 1, "output_tokens": 1}})
    return "".join(json.dumps(line) + "\n" for line in lines)


def message(text):
    return {"type": "agent_message", "text": text}


class FakeCodex:
    """Stands in for subprocess.run: records what codex would be given, and prints `stdout`."""

    def __init__(self, stdout, returncode=0):
        self.stdout, self.returncode, self.seen = stdout, returncode, []

    def __call__(self, cmd, *, input, cwd, env, **kwargs):
        setting = next(arg for arg in cmd if arg.startswith("model_instructions_file="))
        instructions = Path(json.loads(setting.split("=", 1)[1]))
        self.seen.append(
            {
                "instructions": instructions.read_text(),
                "prompt": input,
                "files_in_cwd": list(Path(cwd).iterdir()),
                "api_key": "OPENAI_API_KEY" in env,
            }
        )
        return subprocess.CompletedProcess(cmd, self.returncode, self.stdout, "")


def test_openai_models_go_through_codex_with_paid_openrouter_ids_to_fall_back_on():
    assert MODELS["astra"] == ("codex", "gpt-6-astra")
    assert MODELS["luna"] == ("codex", "gpt-6-luna")
    assert call.OPENROUTER_IDS == {"gpt-6-astra": "openai/gpt-6-astra", "gpt-6-luna": "openai/gpt-6-luna"}
    assert set(call.OPENROUTER_IDS.values()) <= PAID_OK


def login(monkeypatch, which="/opt/homebrew/bin/codex", status="Logged in using ChatGPT", code=0):
    """Fakes `codex` on the PATH (or not, with which=None) and what `codex login status` says."""
    call.codex_ready.cache_clear()
    monkeypatch.setattr(call.shutil, "which", lambda name: which if name == "codex" else None)
    asked = []

    def run(cmd, **kwargs):
        asked.append(cmd)
        return subprocess.CompletedProcess(cmd, code, status, "")

    monkeypatch.setattr(call.subprocess, "run", run)
    return asked


@pytest.mark.parametrize(
    "which, status, code, ready",
    [
        ("/opt/homebrew/bin/codex", "Logged in using ChatGPT", 0, True),
        (None, "", 0, False),  # not installed
        ("/opt/homebrew/bin/codex", "Logged in using an API key", 0, False),  # would bill the key
        ("/opt/homebrew/bin/codex", "Not logged in", 1, False),
    ],
)
def test_codex_ready_needs_the_cli_and_a_chatgpt_login(monkeypatch, which, status, code, ready):
    asked = login(monkeypatch, which, status, code)
    assert (call.codex_ready(), asked) == (ready, [["codex", "login", "status"]] if which else [])
    call.codex_ready.cache_clear()


def test_a_ready_codex_takes_the_openai_models_and_otherwise_openrouter_does(monkeypatch):
    login(monkeypatch)
    ready = [call.route(m) for m in ("astra", "luna", "opus")]
    login(monkeypatch, which=None)
    fallback = [call.route(m) for m in ("astra", "luna", "opus")]
    call.codex_ready.cache_clear()
    assert ready == [("codex", "gpt-6-astra"), ("codex", "gpt-6-luna"), ("claude", "claude-opus-5-5")]
    assert fallback == [
        ("openrouter", "openai/gpt-6-astra"),
        ("openrouter", "openai/gpt-6-luna"),
        ("claude", "claude-opus-5-5"),
    ]


def test_claude_models_are_pinned_to_their_full_ids():
    assert [MODELS[m] for m in ("haiku", "sonnet", "opus")] == [
        ("claude", "claude-haiku-5-5"),
        ("claude", "claude-sonnet-5-5"),
        ("claude", "claude-opus-5-5"),
    ]


def test_openrouter_runs_at_temperature_1_with_room_for_hidden_reasoning():
    body = openrouter_body("z-ai/glm-5.3", "You manage production.", "It is now round 2.")
    settings = (body.get("model"), body.get("temperature"), body.get("max_tokens"))
    assert settings == ("z-ai/glm-5.3", 1.0, 32000)
    assert body.get("messages") == [
        {"role": "system", "content": "You manage production."},
        {"role": "user", "content": "It is now round 2."},
    ]


def test_the_command_pins_model_and_effort_and_shuts_codex_down(tmp_path):
    cmd = codex_command("gpt-6-astra", tmp_path / "instructions.md")
    joined = " ".join(cmd)
    assert cmd[:2] == ["codex", "exec"]
    assert cmd[-1] == "-"  # the prompt comes on stdin
    for part in (
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--ephemeral",
        "--json",
        "-s read-only",
        "-m gpt-6-astra",
        "-c model_reasoning_effort=medium",
        f"-c model_instructions_file={json.dumps(str(tmp_path / 'instructions.md'))}",
        '-c web_search="disabled"',
        "--disable shell_tool",
        "--disable unified_exec",
        "--disable code_mode_host",
    ):
        assert part in joined


def test_the_reply_is_the_last_agent_message_with_the_turns_tokens():
    usage = {"input_tokens": 900, "cached_input_tokens": 600, "output_tokens": 40}
    usage["reasoning_output_tokens"] = 25
    text, meta = codex_reply(events(message("Working it out."), message("DECISION: 20"), usage=usage))
    assert text == "DECISION: 20"
    assert meta == {"prompt_tokens": 900, "completion_tokens": 40, "reasoning_tokens": 25, "tool_calls": 0}


def test_a_tool_the_model_used_is_counted_and_warnings_are_not():
    tool = {"type": "command_execution", "command": "python -c 1"}
    warning, thought = (
        {"type": "error", "message": "Code Mode is unavailable"},
        {"type": "reasoning", "text": "."},
    )
    used = codex_reply(events(tool, message("DECISION: 20")))
    warned = codex_reply(events(warning, thought, message("DECISION: 20")))
    assert (used[1].get("tool_calls"), warned[1].get("tool_calls")) == (1, 0)


def test_lines_that_are_not_json_are_skipped():
    text, _ = codex_reply("Reading prompt from stdin...\n" + events(message("DECISION: 20")))
    assert text == "DECISION: 20"


def test_no_agent_message_fails_with_codexs_reason():
    failed = json.dumps({"type": "turn.failed", "error": {"message": "You've hit your usage limit."}})
    with pytest.raises(CallFailed, match="usage limit"):
        codex_reply(failed + "\n")


def test_codex_gets_the_system_prompt_as_its_instructions_in_an_empty_directory(monkeypatch):
    fake = FakeCodex(events(message("DECISION: 20")))
    monkeypatch.setattr(call.subprocess, "run", fake)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    text, meta = call.call_codex("gpt-6-astra", "You manage production.", "It is now round 2.")
    assert (text, meta.get("reasoning_effort")) == ("DECISION: 20", "medium")
    assert fake.seen == [
        {
            "instructions": "You manage production.",
            "prompt": "It is now round 2.",
            "files_in_cwd": [],
            "api_key": False,
        }
    ]


def test_a_failing_codex_is_tried_three_times_then_reported(monkeypatch):
    fake = FakeCodex(json.dumps({"type": "turn.failed", "error": {"message": "stream disconnected"}}), 1)
    monkeypatch.setattr(call.subprocess, "run", fake)
    monkeypatch.setattr(call.time, "sleep", lambda seconds: None)
    with pytest.raises(CallFailed, match="gpt-6-astra.*stream disconnected"):
        call.call_codex("gpt-6-astra", "system", "prompt")
    assert len(fake.seen) == 3


def test_complete_sends_astra_where_its_route_says(monkeypatch):
    monkeypatch.setattr(call, "call_codex", lambda model_id, *prompts: (f"codex {model_id}", {}))
    monkeypatch.setattr(call, "call_openrouter", lambda model_id, *prompts: (f"openrouter {model_id}", {}))
    monkeypatch.setattr(call, "codex_ready", lambda: True)
    by_codex = call.complete("astra", "system", "prompt")
    monkeypatch.setattr(call, "codex_ready", lambda: False)
    by_openrouter = call.complete("astra", "system", "prompt")
    assert (by_codex, by_openrouter) == (("codex gpt-6-astra", {}), ("openrouter openai/gpt-6-astra", {}))


def test_every_model_has_the_name_a_firm_is_told():
    assert set(call.NAMES) == set(MODELS)
    assert [call.NAMES[m] for m in ("opus", "astra", "glm")] == ["Claude Opus 5.5", "GPT-6 Astra", "GLM-5.3"]
