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

Red/green: write the stubs first (the new names and empty methods), then a test or a few at once, run them and watch every one fail on its assertions, not on an import error, then write the code that passes them. A test that passes on its first run never went red and proves nothing new: delete it, or change it until it fails for the reason you meant. When a task asks for tests of code that already exists, break that code on purpose, watch each test fail, then restore it.

To script what agents do in a test, use `Scripted` from `tests/fakes.py`. PydanticAI's TestModel (`--model test`) calls every tool with placeholder arguments, so the market rejects all its orders.

## Pilots

Smoke tests and pilots of an experiment run on the Claude subscription, never OpenRouter: `--model claude-cli:haiku`. Keep the log when you'll read what the agents were shown and said (only the log has their turns) or need the usage totals; otherwise pass `--no-write`. Commit a log you keep on its own (see Git), and delete the rest.
