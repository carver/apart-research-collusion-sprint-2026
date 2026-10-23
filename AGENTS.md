# Agent notes

## Shared tooling

`.claude/skills/`, `bin/` and `lib/` hold copies of skills, tools and the modules the tools import, from Jason's personal toolbox (`llm-toolbox`), so collaborators without that toolbox can use them. Run a `bin/` tool by its path, e.g. `bin/session-digest`; `-h` gives its options. `bin/apply-edits` makes exact text replacements across files, all or nothing; `bin/bgrun` starts a background job and prints its own PID; `bin/safeps` lists processes by name or command line, and `bin/waitone` waits for one to exit, both skipping their caller; `bin/openrouter-credits` prints the OpenRouter account's credits, bought, used and left; `bin/claude-fresh` makes one locked-down `claude -p` call on the subscription (prompt on stdin), from an empty temporary directory so no CLAUDE.md or settings reach the model. `.claude/settings.json` runs `bin/edit-script-gate` before each Bash call: it refuses an inline Python script that `.replace()`s text in a file and writes it back, and points to `bin/apply-edits`.

`/sprint-paper` (type it; it doesn't fire on its own) takes a sprint project from the rubric to a reviewed report through multi-agent workflows, with the rules that keep long runs from corrupting themselves.

When Jason runs `/upskill`, also list every global tool the session called that isn't in `bin/` (anything from `llm-toolbox/bin` or another personal PATH entry). Pitch copying each into `bin/` from `/home/carver/code/claudedev/llm-toolbox/bin/`; a tool that imports beyond the standard library needs its dependencies added to `pyproject.toml` too. Its path also goes in `REUSE.toml`'s table of llm-toolbox copies, which names Jason alone.

## Git

Commit straight to `main` and push; no branches or PRs. This holds for every collaborator. In a `/build`, the commits stay local until its review and refactor are done, then go up together.

Run logs (`logs/`) go in a commit of their own, with nothing else in it. Hold that commit back until Jason or Thomas have reviewed the logs, and tell him it's waiting. Commits made after it wait too; to push them sooner, move them below it and push up to the last of them (`git push origin <sha>:main`).

## Checks

Committing runs the pilot lock (`bin/pilot-lock`) and ruff, and for agents the lock check on `uv.lock`, the tests, pyright and the license check (`reuse lint`) too (`bin/git-pre-commit`, `bin/agent-pre-commit`), so don't run them first: commit and read the hook's output. Link the hooks in once per clone, as `bin/git-pre-commit`'s header shows.

Each file takes its license from `REUSE.toml`: MIT for the code paths it lists, CC-BY-4.0 for everything else. Code in a new place (a new folder, or a new kind of file) needs its path added there. Otherwise it falls under CC-BY-4.0, and no check notices.

## Tests

Red/green: write the stubs first (the new names and empty methods), then a test or a few at once, run them and watch every one fail on its assertions, not on an import error, then write the code that passes them. A test that passes on its first run never went red and proves nothing new: delete it, or change it until it fails for the reason you meant. When a task asks for tests of code that already exists, break that code on purpose, watch each test fail, then restore it.

## Pilots

Smoke tests and pilots of an experiment run on the Claude subscription, never OpenRouter: `uv run zcc run <criterion> --models haiku --out /tmp/smoke.jsonl`. Without `--out` the replies go into `logs/<criterion>/`, which should hold only runs you mean to keep. Commit a log you keep on its own (see Git).

## Criteria

Jason and Thomas each own one of the four criteria at a time (README, "The four criteria"; the owner is on the criterion's sub-issue of #38). Work on a criterion stays inside `zerocommcartel/criteria/<criterion>/`, its tests (`tests/test_criterion_<criterion>.py`) and `logs/<criterion>/`. Anything else in `zerocommcartel/` is the shared core. Change it only when a criterion can't do its job without the change, put the change in a commit of its own, and say so on #38 so the other owner pulls before building on it. `uv run zcc hashes`, diffed from before and after, shows which logs a change leaves stale.

`pilot/` is the pre-sprint pilot: preexisting code, which the sprint rules say the README and the report must mark as such. It is frozen at the tag `pilot-frozen`, and `bin/pilot-lock` refuses commits that change it, its logs or its tests. Don't unlock it (`PILOT_UNLOCK=1`) unless Jason or Thomas asks you to. It holds the code written before the sprint plus three bug fixes from its first day (#37). New code goes in `zerocommcartel/`.
