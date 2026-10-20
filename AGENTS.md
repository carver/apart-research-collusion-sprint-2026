# Agent notes

## Shared tooling

`.claude/skills/` and `bin/` hold copies of skills and tools from Jason's personal toolbox (`llm-toolbox`), so collaborators without that toolbox can use them. Run a `bin/` tool by its path, e.g. `bin/session-digest`.

When running `/upskill`, also list every global tool the session called that isn't in `bin/` (anything from `llm-toolbox/bin` or another personal PATH entry). Pitch copying each into `bin/` from `/home/carver/code/claudedev/llm-toolbox/bin/`; a tool that imports beyond the standard library needs its dependencies added to `pyproject.toml` too.

## Git

Commit straight to `main` and push; no branches or PRs. This holds for every collaborator.

Run logs (`logs/`) go in a commit of their own, with nothing else in it. Hold that commit back until Jason has reviewed the logs, and tell him it's waiting. Commits made after it wait too; to push them sooner, move them below it and push up to the last of them (`git push origin <sha>:main`).

## Checks

Committing runs ruff, and for agents the tests and pyright too (`bin/git-pre-commit`, `bin/agent-pre-commit`), so don't run them first: commit and read the hook's output. Link the hooks in once per clone, as `bin/git-pre-commit`'s header shows.

## Tests

Red/green: write a test, or a few at once, run them and watch every one fail, then write the code that passes them. A test that passes on its first run never went red and proves nothing new: delete it, or change it until it fails for the reason you meant.

To script what agents do in a test, use `Scripted` from `tests/fakes.py`. PydanticAI's TestModel (`--model test`) calls every tool with placeholder arguments, so the market rejects all its orders.

## Pilots

Smoke tests and pilots of an experiment run on the Claude subscription, never OpenRouter: `--model claude-cli:haiku --no-write`. Drop `--no-write` only when you need the usage totals, and delete that log afterwards.
