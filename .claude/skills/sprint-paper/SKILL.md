---
name: sprint-paper
description: Carry a research-sprint project from rubric to a finished report with multi-agent workflows: scope, pilot, runs, robustness, novelty, writing, review.
disable-model-invocation: true
---

# Sprint paper

The goal is a report that scores top marks on the sprint's rubric. Every stage below serves one of its three dimensions: Impact & Innovation, Execution Quality, Presentation & Clarity. Plan all stages from the start: novelty and robustness bolted on after the draft cost a restart. Each stage is one Workflow run (see `templates/`). Read each run's result before designing the next.

Read [orchestration.md](orchestration.md) before launching the first workflow: it has the rules that keep a long multi-agent run from corrupting itself. Read [levers.md](levers.md) at stage 1 and again before writing.

## Stages

1. **Rules.** Fetch the live sprint page's Guidelines tab and the official template. The rules change during a sprint: on 2026-10-21 the AI-writing rule, the abstract length and question 1.3 all changed. Write a requirements note covering the page cap, abstract length, required appendices, AI-use rule, prior-work disclosure and template layout. Done when the note quotes the live page and gives its fetch date.
2. **Scope** (`templates/1-scope.js`). Gather: a rubric brief, a map of the team's prior work, literature sweeps (one agent per area), an infra scout. Then: ideators with distinct lenses, a merge, an adversarial novelty check and a feasibility check per candidate, a rubric judge panel, a selection. Done when one direction is chosen, with its hypotheses, GO rules for the pilot and a fallback, written in `notes/ideas/selection.md`.
3. **Build and pilot** (`templates/2-build-pilot.js`). Parallel builders on disjoint files, then harness, measurement and design reviewers, a fixer, the pilot, and an adversarial audit that recomputes every GO number from raw logs. Done when the audit agrees with the GO decision, or the fallback is taken and logged.
4. **Main runs and measurement.** Long jobs run as `bgrun --wait -o LOG -- CMD` in a background call, each resumable. Meanwhile run a workflow for analysis code, figures, extra cells and the paper scaffold (`templates/3-extend.js`). Done when every measure in the design exists for every cell.
5. **Mechanism and robustness** (`templates/4-mechanism.js`, `5-robustness.js`). Explain the headline (coded reasoning with a gold set labelled before the coder runs, then a verifier). Stress-test it: controls that isolate the active ingredient, a dose ladder, a placement control, same-time anchor days against drift, a second model family. Done when the headline survives its controls or the paper's claim shrinks to what does.
6. **Paper** (`templates/6-paper.js`):
   1. final analysis plus a numbers ledger (`paper/numbers.json`: every citable number with its source file), and an independent recomputation that imports none of the analysis code;
   2. an adversarial novelty sweep, one agent per finding, whose report binds what the paper may claim;
   3. competing framings scored by rubric judges, then a claims plan;
   4. the writer;
   5. reviewers: three rubric judges, a fact-checker against the ledger, prose and template, novelty with fresh searches, citations;
   6. a reviser, then a cold final judge.

   Done when the final judge's checklist passes: abstract length, page cap, no TODO markers, every figure referenced, required appendices present, every number in the ledger.
7. **Teaching pages**, optional (`templates/7-teach.js`): an explorer, a results dashboard and a guided tutor, rebuilt from the final results.

## Templates

`templates/*.js` are the scripts from a full run (2026-10-21/22, `../apart-oneshot-collusion`). Their paths, cells and study details are that run's. Keep their structure (stages, schemas, reviewer lenses, gates) and rewrite the context block and the tasks for the new study.
