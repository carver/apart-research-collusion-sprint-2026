# Rubric levers

What raises each rubric dimension to a 5, and which stage delivers it. Check every item at stage 1, when planning, and again before writing.

## Impact & Innovation

- **Novelty that survives an adversarial search.** Before framing, give one agent per finding at least 8 differently phrased searches (arXiv, Scholar, OpenReview, LessWrong and the Alignment Forum, lab blogs, past Apart submissions), defaulting to "partially scooped". After writing, a reviewer repeats the search with new phrasings. The paper claims only what survives, and cites the closest work.
- **Theory of change.** Name who acts on the result (evaluators, model providers, regulators, other researchers) and what they should do differently. Map the result to the sprint's own numbered questions.
- **Something others can build on:** a tool, a checklist, a dataset or a harness, released with the paper.

## Execution Quality

- A positive control that runs in the same sessions, and a negative control or baseline.
- Judges and coders validated on a gold set labelled before they run, with agreement or kappa reported. State that model-written gold labels are model-written.
- Session-clustered statistics (sessions as the unit), seeds, variance, and multiple-comparison correction across the tests the paper reports. Report nulls and results in the opposite direction.
- **The headline gets its own controls.** A striking effect found by accident is exploratory until it has them: a matched control isolating the active ingredient, a dose or word ladder, same-time anchors, a second model family, more days on noisy cells.
- An independent recomputation of the key numbers by an agent that doesn't import the analysis code.

## Presentation & Clarity

- One hero figure that carries the headline. Every caption stands alone. A plain-language "what we found" sentence or box.
- A page budget set before writing (for example: intro and related work 1.25 pages, methods 1.5, results 2.5-2.75, discussion 0.75); move detail to appendices.
- Every number traces to the ledger and every citation to a source someone read. A made-up result or reference can disqualify the project.
- Prose a careful researcher would write: concrete, short sentences, no padding. Run the `unslop` skill over it.

## Required by the rules (check the live page)

- The abstract's word range, the page cap, the official template, and the authors and affiliations block.
- A "Limitations and Dual-Use / Ethical Considerations" appendix. Ask whether the finding makes collusion easier to carry out or harder to detect, including making a model *look* compliant in evaluations.
- Prior-work disclosure: everything built before the sprint, marked as preexisting in the README and the report.
