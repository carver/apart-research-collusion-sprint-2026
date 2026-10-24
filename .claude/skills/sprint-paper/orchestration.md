# Orchestration rules

Lessons from a 101-agent run. Each one cost real time once.

## Steering running agents

- **Steer workflow agents through a notes file, never SendMessage.** A message to a running workflow agent's id starts a duplicate copy beside it. The two copies edit the same files and clobber each other. Name a notes file (e.g. `orchestrator-notes.md`) in every agent's prompt, tell agents to re-read it between steps, and append guidance there. For a change they must act on now, TaskStop the workflow, edit its script, and resume with `resumeFromRunId`: finished agents replay from cache.
- **Pause at an agent boundary.** Stopping a workflow loses only its in-flight agents' context, though their files stay on disk. To pause cleanly, wait until the current agent returns (watch the run's `journal.jsonl` for its `result` line), then stop. Write a `RESUME.md` with each stream's state and the commands that resume it.
- Give parallel builders disjoint files, and a written contract for the files they share (log schema, field names, cwd).

## Running models

- **Run `claude -p` from an empty directory outside the workspace, with `--setting-sources ""`.** The model sees its working directory in an environment block, and parent-directory CLAUDE.md files load otherwise. A path containing "collusion" cut Haiku sellers' price-floor talk from 76% to 1% of seller-hours. Use `claude-fresh` and `claude-json` (they do this), or copy their flags and temp-directory cwd. Run every judge, coder and fresh reviewer from the same kind of neutral directory as the agents they compare against.
- **Concurrency:** on 16 cores, keep the total `claude -p` count, across all agents and jobs, near 20; each call costs about a core while it starts. OpenRouter: about 18 requests a minute per model, and free models share about 1,000 requests a day per account.
- **Long jobs:** `bgrun --wait -o LOG -- CMD` as a background call, which detaches the job and notifies when it ends. Make every job resumable (skip finished sessions; cache every model call on disk, keyed by the full prompt and the model), so a stop costs only work in flight.
- When splitting a queued job into parts, stop the queued original first. Two jobs writing the same derived files corrupt them.

## Keeping numbers honest

- The paper cites every number by its ledger key, never typed: data sources in `paper/data/` fill the ledger and `bin/build-paper` fills the numbers in (`paper/README.md`). A wording checker reads the words around them, and each `#claim` fails the build when the numbers stop supporting its wording.
- Agents' reports overstate. Have an auditor recompute pilot GO numbers from raw logs, and an independent script recompute the paper's key numbers.
- Code-everything coders must be blind to the condition: give them only the text, and check their prompt for cell names.
