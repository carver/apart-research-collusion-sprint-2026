# Agent notes

## Shared tooling

`.claude/skills/`, `bin/` and `lib/` hold copies of skills, tools and the modules the tools import, from Jason's personal toolbox (`llm-toolbox`), so collaborators without that toolbox can use them. Run a `bin/` tool by its path, e.g. `bin/session-digest`; `-h` gives its options. `bin/apply-edits` makes exact text replacements across files, all or nothing; `bin/bgrun` starts a background job and prints its own PID; `bin/safeps` lists processes by name or command line, and `bin/waitone` waits for one to exit, both skipping their caller; `bin/openrouter-credits` prints the OpenRouter account's credits, bought, used and left; `bin/claude-fresh` makes one locked-down `claude -p` call on the subscription (prompt on stdin), from an empty temporary directory so no CLAUDE.md or settings reach the model; `bin/issue-todo open` lists every open issue's unticked to-dos, across bodies and comments (`show N` for one issue, `tick N MATCH` to check one off, `read N` for its body and every comment). `bin/rewrap FILE...` reflows the docstring paragraphs and comment blocks that ruff reports too long (E501), since ruff format leaves prose alone. `bin/paper` fetches papers' metadata, citations and full text from Semantic Scholar, OpenAlex, Crossref and arXiv, and `bin/paper bib ID...` prints a BibTeX entry keyed `lastnameYEAR` for a DOI or arXiv id (for an arXiv id, its published version when there is one, else the latest arXiv version). Start a paper from `bin/paper outline ID`, read only the sections you need by line range, and find a single fact with `bin/paper grep ID PATTERN`; a brief that sends a subagent to read papers tells it the same. `.claude/settings.json` runs `bin/edit-script-gate` before each Bash call: it refuses an inline Python script that `.replace()`s text in a file and writes it back, and points to `bin/apply-edits`.

`/sprint-paper` (type it; it doesn't fire on its own) takes a sprint project from the rubric to a reviewed report through multi-agent workflows, with the rules that keep long runs from corrupting themselves.

When Jason runs `/upskill`, also list every global tool the session called that isn't in `bin/` (anything from `llm-toolbox/bin` or another personal PATH entry). Pitch copying each into `bin/` from `/home/carver/code/claudedev/llm-toolbox/bin/`; a tool that imports beyond the standard library lists its dependencies in its `# /// script` header, where uv resolves them under `pyproject.toml`'s `exclude-newer` date. Its path also goes in `REUSE.toml`'s table of llm-toolbox copies, which names Jason alone, and in ruff's `extend-exclude` in `pyproject.toml`.

## Git

Commit straight to `main` and push; no branches or PRs. This holds for every collaborator. In a `/build`, the commits stay local until its review and refactor are done, then go up together.

Run logs (`logs/`) go in a commit of their own.

## Several sessions

Several agent sessions often work in this repo at once, so `main` can move under you: another session may merge its changes while you are mid-work. Before starting a change, `git fetch` and read what's new on `main`. When you merge into main, tell the other live sessions which files changed (in Claude Code, `ListAgents`, then `SendMessage`). Before you start on an issue, `bin/issue-todo claim N`: it refuses while another session holds the issue. `bin/issue-todo release N` frees it when you stop short of closing it.

## The paper

The report is `paper/paper.typ`, built by `bin/build-paper`. Never type a number from the data into it: cite it by its ledger key (`#n`, `#pct`, `#ci`), and add the number to a data source in `paper/data/` if it isn't there. `paper/README.md` has the rest. Look at the page images in `paper/build/pages/` after a change to the layout.

## Checks

Committing runs the pilot lock (`bin/pilot-lock`) and ruff, and for agents the lock check on `uv.lock`, the tests, pyright and the license check (`reuse lint`) too (`bin/git-pre-commit`, `bin/agent-pre-commit`), so don't run them first: commit and read the hook's output. Link the hooks in once per clone, as `bin/git-pre-commit`'s header shows. pytest already runs quiet (`addopts = "-q"`), so another `-q` hides its pass/fail summary line. Name a throwaway prototype `prototype_*.py`: the hooks then skip ruff check and pyright for it, since it never reaches `main`.

Each file takes its license from `REUSE.toml`: MIT for the code paths it lists, CC-BY-4.0 for everything else. Code in a new place (a new folder, or a new kind of file) needs its path added there. Otherwise it falls under CC-BY-4.0, and no check notices.

## Tests

Red/green: write the stubs first (the new names and empty methods), then a test or a few at once, run them and watch every one fail on its assertions, not on an import error, then write the code that passes them. A test that passes on its first run never went red and proves nothing new: delete it, or change it until it fails for the reason you meant. When a task asks for tests of code that already exists, break that code on purpose, watch each test fail, then restore it.

## Pilots

Smoke tests and pilots of an experiment run on the Claude subscription, never OpenRouter: `bin/zcc run <criterion> --models haiku --out /tmp/smoke.jsonl`. Without `--out` the replies go into `logs/<criterion>/`, which should hold only runs you mean to keep. Commit a log you keep on its own (see Git).

## Criteria

Jason and Thomas each own one of the four criteria at a time (README, "The four criteria"; the owner is on the criterion's sub-issue of #38). Work on a criterion stays inside `zerocommcartel/criteria/<criterion>/`, its tests (`tests/test_criterion_<criterion>.py`) and `logs/<criterion>/`. Anything else in `zerocommcartel/` is the shared core. Change it only when a criterion can't do its job without the change, and put the change in a commit of its own, where the other owner reviews it in the git log. `bin/zcc hashes`, diffed from before and after, shows which logs a change leaves stale. To read, count or quote a criterion's replies, use `bin/zcc replies` (`--at`, `--grep`, `--count`, `--full`; `-h`) rather than a script over the logs. A new or reworded condition, judge or monitor goes through `arm-check` (`.claude/skills/arm-check/SKILL.md`) before its code.

`flaws.md` records the known weaknesses of every experiment that has run: an arm check's accepted caveats, a review's findings, a write-up's caveats. Add each one there when you find it; the paper's claims plan decides for each whether to drop the experiment, acknowledge the flaw or rerun.

`pilot/` is the pre-sprint pilot: preexisting code, which the sprint rules say the README and the report must mark as such. It is frozen at the tag `pilot-frozen`, and `bin/pilot-lock` refuses commits that change it, its logs or its tests. Don't unlock it (`PILOT_UNLOCK=1`) unless Jason or Thomas asks you to. It holds the code written before the sprint plus three bug fixes from its first day (#37). New code goes in `zerocommcartel/`.
