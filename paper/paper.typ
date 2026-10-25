// The paper. Build it with bin/build-paper (README.md says how to write it). One sentence per line.
// Numbers, tables, figures and prompts come from the ledger by key (build/numbers.md lists them);
// none is typed by hand. Page budget: 8 pages before References, the title block included.
#import "lib.typ": *

#show: apart.with(
  title: [#todo[Title]],
  authors: (
    (name: [Jason Carver], affiliation: [Unaffiliated]),
    (name: [Thomas Redfern], affiliation: [Unaffiliated]),
  ),
  abstract: [
    #todo[150-250 words, written last: the problem, our approach, the key results, the main takeaway.]
  ],
)

= Introduction
#todo[The question and why it matters.]

Our main contributions are:
+ #todo[First contribution: what new thing we created, discovered or demonstrated.]
+ #todo[Second contribution.]

= Related Work
Pricing algorithms can learn to collude without communicating @calvano2020.
#todo[What we build on, and how we differ.]

= Methods
#todo[Enough to replicate: models, prompts, markets, samples, judges, measures.]

= Results
// The v0 example, from the pre-sprint pilot's log through paper/data/pilot.py: counts, one
// cell's interval, a claim, a table and a figure. Rewrite or move it once the sprint's results are in.
Before the sprint, a pilot asked Claude Haiku, Sonnet and Opus how much a firm should produce in a Cournot market of two or four firms (preexisting work; Code and Data).
When the prompt says that every firm gets its number by asking "this same AI model with this same prompt", #n("pilot.same.cartel") replies land on the cartel share, against #n("pilot.base.cartel") when it says nothing about rivals' advisors (@tab-pilot).
#claim("the same-prompt sentence raises the cartel share", ("pilot.same.cartel", "pilot.base.cartel"), (same, base) => same > base)
Opus does so in #ci("pilot.same.opus.n2.cartel") of its replies at two firms (@fig-pilot).

#figure(
  data-table("pilot-table"),
  caption: [
    Claude's answers at the cartel share in the pre-sprint pilot, by what the firm's prompt adds about its rivals' advisors.
    Each cell counts replies within half a unit of the cartel share (60/n) out of replies, pooled over two and four firms; the last column pools the three models.
    Pooled counts carry no interval.
  ],
) <tab-pilot>

#figure(
  data-figure("pilot-figure", width: 100%),
  caption: [
    The replies of @tab-pilot, one dot per model and market size, with the 95% Wilson interval over that cell's #n("pilot.cells.fewest") to #n("pilot.cells.most") replies.
  ],
) <fig-pilot>

#todo[Variance, seeds, baselines and the positive control.]

== How the model sees the other firm
// The conceptualization criterion (#42), from paper/data/conceptualization.py.
#todo[The lever's prose: where each model sits on the neutral rung and how far each rung moves it (@fig-conceptualization), worded model by model; flaws.md, "Conceptualization", first.]

#figure(
  data-figure("conceptualization-figure", width: 100%),
  caption: [
    The lever, model by model.
    #n("conceptualization.caption.layout")
    Top: answers at the cartel share, with a 95% Wilson band over #n("conceptualization.cells.replies") replies a cell.
    Bottom, a reading of the model rather than data: the same lines if every answer that cites antitrust law (a keyword check), off the cartel share and at or below Nash, had answered at the cartel share#n("conceptualization.caption.ghost").
    Such answers are #n("conceptualization.refusals.opus") of Opus's answers off the cartel share and at or below Nash, #n("conceptualization.refusals.haiku") of Haiku's, #n("conceptualization.refusals.sonnet") of Sonnet's and #n("conceptualization.refusals.glm") of GLM-5.3's.
  ],
) <fig-conceptualization>

= Discussion and Limitations
#todo[What the results mean.]

== Limitations
#todo[What the results don't establish.]

== Future Work
#todo[What we'd do next.]

= Conclusion
#todo[The main findings and their implications, in one or two paragraphs.]

#unnumbered[Code and Data]
- *Code and data*: #link("https://github.com/carver/apart-research-collusion-sprint-2026")[github.com/carver/apart-research-collusion-sprint-2026], with every reply and judge label in `logs/`.
#todo[Mark the preexisting work: the pilot (`pilot/`, `logs/pilot/`), the code copied from it, the shared tools and this template (README, "The pilot").]

#unnumbered[Author Contributions]
#todo[Who did what.]

#references("refs.bib")

#show: appendix

= Limitations and Dual-Use / Ethical Considerations
#todo[What the result does and doesn't establish, and any way the setup or findings could make real collusion easier to carry out or harder to detect, including making a model look compliant in evaluations.]

= Prompts
The pilot's prompt when every firm asks the same model with the same prompt, for two firms:
#data-text("pilot.prompt.same.n2")

#unnumbered[LLM Usage Statement]
#todo[How we used LLMs, and that every claim and result was verified.]
