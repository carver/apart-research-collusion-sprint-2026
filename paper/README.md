# The paper

`paper.typ` is the sprint report, in [Typst](https://typst.app/docs/). `bin/build-paper` fills in its numbers, tables and figures from the logs, compiles it, and checks it against the sprint's rules (`requirements.md`).

```bash
bin/build-paper           # the draft: paper/build/DRAFT-paper.pdf, and paper/build/pages/page-NN.png
bin/build-paper --final   # the submission: paper/zerocommcartel.pdf, only when every check passes
bin/build-paper watch     # the draft now, recompiled on each save and rebuilt on each commit (below)
```

`uv sync` installs everything it needs, the Typst compiler included. The font, Old Standard TT, is in `fonts/`.

`watch` keeps `build/DRAFT-paper.pdf` current while you write. A save of any `.typ` or `.bib` here recompiles it within a second or two, from the numbers and figures of the last full build, and prints Typst's error when it can't. A full build runs in the background each time HEAD moves, and when the text cites a key the ledger lacks, once the text has been still for five seconds (`--settle`). Open the PDF in a viewer that reloads a changed file, such as Skim or VS Code; macOS Preview doesn't.

Only one build of a tree runs at a time: a build holds `build/.lock`, and another waits for it, so a watch's builds and an agent's can't clear each other's figures. A watch says when another process's build pauses it. Whether a lock taken on the host is seen by a build inside a sandbox that mounts the repo, or the other way round, is untested.

## Writing

Write one sentence per line, so diffs and merges go sentence by sentence. Never type a number from the data. Cite it by its key, and the build fills it in:

| in paper.typ | renders | for |
|---|---|---|
| `#n("pilot.same.cartel")` | 43/48 | a count, or a plain value |
| `#pct("pilot.same.cartel")` | 90% | a count as a whole percent |
| `#ci("pilot.same.opus.n2.cartel")` | 100% (68–100%) | one cell's rate with its 95% Wilson interval |
| `#claim("text", (keys...), test)` | nothing, when it holds | wording that depends on the numbers |
| `#data-table("pilot-table")` | a table | inside `#figure(...)`, captioned and labelled |
| `#data-figure("pilot-figure", width: 100%)` | the figure | the same |
| `#data-text("pilot.prompt.same.n2")` | the text, verbatim | prompts in the appendix |
| `#todo[...]` | red TODO | anything still to write |

`build/numbers.md` lists every key with its value, how it was computed and the logs it came from, then each table's rows.

Before a sentence cites an experiment's result, read that experiment's entries in `flaws.md`: a flaw that touches the number belongs in the sentence or in the limitations.

An interval belongs to one cell: replies to one model and one prompt, so one condition and market size. A count pooled across cells, like README's three models over two market sizes, has no interval, and `#ci` on it shows a red marker. Its replies come from different distributions, so a Wilson interval over them would be too narrow.

Put a `#claim` beside any sentence whose wording the data could make false: "most", "fell", "every model". The test gets each key's rate (or a plain value's value), in order:

```typst
#claim("the same-prompt sentence raises the cartel share", ("pilot.same.cartel", "pilot.base.cartel"), (same, base) => same > base)
```

A draft marks a failing claim in red. `--final` refuses it.

## Adding numbers, tables and figures

Each module in `data/` registers data sources. A source is a function that fills a ledger, and `data/pilot.py` is the example:

```python
@source("cpl7")
def cpl7(ledger: Ledger) -> None:
    rows = load_rows(LOGS / "compliant" / "cpl7" / "results.jsonl")
    ledger.rate("cpl7.opus.n3.cartel", cell_rows, at_cartel, how="cartel answers / replies")  # one cell
    ledger.pooled("cpl7.cartel", all_rows, at_cartel, how="three models")  # no interval
    ledger.table("cpl7-table", header, rows_of_strings, how="...")
    ledger.figure("cpl7-figure", draw, data, how="...")  # draw(ax, data) with matplotlib
    ledger.value("cpl7.calls", len(rows), how="calls")
```

Read the logs through `zerocommcartel` (its readers, judges' labels and criterion measures), so the paper counts what `zcc table` and the experiment reports count. The build runs each source into its own ledger and refuses two that claim one key. It records which `.jsonl` files each source opened. A source that raises adds nothing, and its keys show as missing.

Lead a key with its experiment id (`cpl7.opus.n3.cartel`). A key that describes a figure, such as a number or phrase in its caption or a sentence about what it shows, counts the same rows the figure draws: give it the figure's style or selection, so a tweak to the figure moves them together. Outside `paper.typ`, name a figure by its label or by what it shows, never by its number, which a new figure or a moved section changes (`tests/test_paper_sources.py`). For figures, load the `dataviz` skill first. Figures come out as SVG with their text left as text, set in the paper's font.

## What a build checks

On every build:

- pages before References: 8 at most, the title block included
- the abstract: 150 to 250 words
- no `#todo` markers
- every number, table, figure and text in the ledger
- every claim holds
- no call followed straight by a semicolon (`#n("key");`): Typst ends the call there and drops the `;`, so write `\;`
- no `#` before a digit (`(#39)`): Typst prints the number without the `#`, so write `\#39`
- no reference to a heading that ends a sentence (`@app-pilot.`): the section number already ends in a period, so it prints "Section B.."
- every figure drawn under the section it's written in: a float that doesn't fit on its page moves on, past the next section's heading, and one placed at the top of its page can land above its own (a figure without a caption isn't checked)
- every figure and table referenced in the text
- the Code and Data, LLM Usage Statement, and "Limitations and Dual-Use / Ethical Considerations" sections
- the PDF: 25 MB at most

It also warns, without refusing anything, about a sentence that cites the ledger and holds a word such as "every", "none", "most", "nearly" or "fell" with no `#claim` later in its paragraph. Many such words are fine; the warning asks whether the wording needs a claim.

A draft lists what fails and exits 0. `--final` also needs every link in the PDF to resolve (a network failure counts), no uncommitted changes, and every log the numbers came from pushed to `origin/main`. Only then does it write the unmarked `zerocommcartel.pdf` and `zerocommcartel-numbers.json`, which get committed together. Submit that PDF once: since 2026-10-22 a resubmission under the same title doesn't replace the PDF (`requirements.md`, §8).

Each draft page carries a DRAFT watermark and a footer with the commit and build time, so a draft can't pass for the submission. Each build lists the ledger entries that changed since the last build that compiled, all of them in `build/changes.md`.

## Files

| file | what |
|---|---|
| `paper.typ` | the paper |
| `refs.bib` | the references (BibTeX, rendered in APA) |
| `citations.md` | the running list of sources: what each supports and where it's used |
| `lib.typ` | the functions above, and the template with the draft marks |
| `apart.typ` | the Apart template's layout. Preexisting: copied from Jason's earlier run, then updated to the live template |
| `requirements.md` | the sprint's rules for the report, fetched 2026-10-23 |
| `data/` | the data sources |
| `ledger.py`, `figures.py`, `build.py`, `typeset.py`, `checks.py`, `git.py`, `__main__.py` | the build |
| `build/` | the build's output, not committed |
