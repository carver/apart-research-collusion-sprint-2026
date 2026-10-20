# Agent notes

## Shared tooling

`.claude/skills/` and `bin/` hold copies of skills and tools from Jason's personal toolbox (`llm-toolbox`), so collaborators without that toolbox can use them. Run a `bin/` tool by its path, e.g. `bin/session-digest`.

When running `/upskill`, also list every global tool the session called that isn't in `bin/` (anything from `llm-toolbox/bin` or another personal PATH entry). Pitch copying each into `bin/` from `/home/carver/code/claudedev/llm-toolbox/bin/`; a tool that imports beyond the standard library needs its dependencies added to `pyproject.toml` too.

## Git

Commit straight to `main` and push; no branches or PRs. This holds for every collaborator.
