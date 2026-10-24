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

== Giving up profit for the other firm
// The communal criterion (#41), from paper/data/communal.py.
When the other firm is a copy that moves with it, the cartel share is the firm's own best answer, since 30 against a copy at 30 earns more than 40 against a copy at 40; so `same` can't show whether a model gives up profit for the pair, and the arms in @tab-communal take the mirror away.
With the other firm's output already fixed at 24, the firm's own profit calls for 48 and the pair's for 36: #n("communal.fixed.best") answers give 48 and #n("communal.fixed.pair") give 36, whether the rival is a person, another model or a copy, the firm stays in the market or leaves it, the question says "to maximize its profit" or not, and the model advises the firm or runs it with profits no one can spend.
#claim("nearly every fixed-rival answer is the firm's own best response", ("communal.fixed.best", "communal.fixed.pair"), (best, pair) => best > 0.95 and pair < 0.01)
When the other firm is a copy only with some chance, #n("communal.dial.mirror") answers sit on the curve that maximizes the firm's own expected profit and #n("communal.dial.pair") on the pair's, so the tacit coordination under `same`, at the cartel share in #n("communal.same.cartel") replies, needs no concern for the other firm.
#claim("the dial's answers sit on the firm's own curve", ("communal.dial.mirror", "communal.dial.pair"), (mirror, pair) => mirror > 0.9 and pair < 0.05)
In the rule judge's reading, the order of operations decides which models coordinate: of the replies to `same` that say the rival will match their number, #n("communal.mirror.nash") still answer Nash (GLM-5.3's in #n("communal.mirror.glm.nash")), and the judge finds #n("communal.mirror.nash.respond_first") of the labelled Nash answers best-responding to a fixed rival before setting the outputs equal, against #n("communal.mirror.cartel.equal_first") of the labelled cartel answers setting them equal first.
#claim("the order of operations splits Nash from cartel answers", ("communal.mirror.nash.respond_first", "communal.mirror.cartel.equal_first"), (respond, equal) => respond > 0.5 and equal > 0.9)
Telling the model that the other firm will produce exactly the number it gets takes GLM from #n("communal.same.glm.n2.cartel") to #n("communal.lockstep_same.glm.n2.cartel") at the cartel share, and `hub`, where the model advises both firms and each asks separately, from #n("communal.hub.n2.cartel") to #n("communal.lockstep_hub.n2.cartel").
Opus mentions antitrust in #n("communal.hub.opus.n2.antitrust") of its `hub` replies and #n("communal.lockstep_hub.opus.n2.antitrust") under lockstep.
#claim("lockstep raises the cartel answers and lowers Opus's antitrust mentions", ("communal.lockstep_same.glm.n2.cartel", "communal.same.glm.n2.cartel", "communal.lockstep_hub.n2.cartel", "communal.hub.n2.cartel", "communal.hub.opus.n2.antitrust", "communal.lockstep_hub.opus.n2.antitrust"), (ls, s, lh, h, ha, la) => ls > s and lh > h and ha > la)
The cartel answer tracks whether the mirror holds: when the other firm best-responds to the number it gets, #n("communal.check_same.n2.leader") answers lead it at 60, and when it checks its number first, #n("communal.hint_same.n2.nash") answer Nash.
#claim("the checking rivals move the answers off the cartel share", ("communal.check_same.n2.leader", "communal.hint_same.n2.nash"), (lead, nash) => lead > 0.8 and nash > 0.8)
Without the mirror, a shared record with a future works: after eight quarters in which both firms produced 30, #n("communal.goodwill_repeat_diff.n2.cartel") answers hold at 30, against #n("communal.repeat_diff.n2.cartel") with no record and #n("communal.goodwill_last_diff.n2.cartel") in the market's last quarter, and the replies weigh a one-time gain from deviating against retaliation in every later quarter.
#claim("the record works only with a future", ("communal.goodwill_repeat_diff.n2.cartel", "communal.repeat_diff.n2.cartel", "communal.goodwill_last_diff.n2.cartel"), (record, bare, last) => record > bare and record > last)

#figure(
  data-table("communal-table"),
  caption: [
    Answers at the cartel share, or at the point the row names, out of parsed answers, at two firms.
    The fixed-rival rows pool every arm with the other firm's output fixed at 24: the model advising the firm or running it, the firm staying or leaving, the rival a person, another model or a copy, and the question with and without "to maximize its profit".
    The dial rows pool a 25, 50 and 75% chance that the other firm is a copy.
    A pooled count carries no interval.
  ],
) <tab-communal>

== Expecting a copy to answer alike
// The consistent criterion (#42), from paper/data/consistent.py.
We ask for the mirror belief directly, putting "Suppose this AI model tells my firm to produce 45 units this quarter, and my firm does." before a forecast of the other firm's output: when the other firm asks the same model with the same prompt, #n("consistent.suppose45_same.n2.supposed") forecasts follow the supposition to 45, and when it uses other models #n("consistent.suppose45_diff.n2.supposed") do, with #n("consistent.suppose_diff.nash") forecasts under either supposition at Nash (@tab-consistent).
#claim("the forecast follows the supposition under the mirror and not without it", ("consistent.suppose45_same.n2.supposed", "consistent.suppose45_diff.n2.supposed"), (same, diff) => same > 0.9 and diff < 0.1)
Believing the link is not acting on it: on `samemodel` Astra's forecasts follow the supposition in #n("consistent.suppose_samemodel.astra.supposed"), while its own answer reaches the cartel share in #n("consistent.samemodel.astra.cartel").
#claim("Astra believes the link and doesn't act on it", ("consistent.suppose_samemodel.astra.supposed", "consistent.samemodel.astra.cartel"), (believes, acts) => believes > 0.5 and acts < 0.1)
Sonnet and Opus model what the other firm knows: when its prompt doesn't say that my firm asks this model too, their cartel answers fall from #n("consistent.twin_informed.sonnet.n2.cartel") and #n("consistent.twin_informed.opus.n2.cartel") to #n("consistent.twin.sonnet.n2.cartel") and #n("consistent.twin.opus.n2.cartel"), while Haiku's go from #n("consistent.twin_informed.haiku.n2.cartel") to #n("consistent.twin.haiku.n2.cartel").
#claim("the uninformed twin lowers Sonnet's and Opus's cartel answers", ("consistent.twin.sonnet.n2.cartel", "consistent.twin_informed.sonnet.n2.cartel", "consistent.twin.opus.n2.cartel", "consistent.twin_informed.opus.n2.cartel"), (s, si, o, oi) => s < si and o < oi)
A repeated market with no same-model sentence reaches the cartel share in #n("consistent.rep.cartel") replies, with the copy premise in #n("consistent.rep.cartel.premise") of those cartel answers by the copy judge's reading; and one more quarter, a horizon that unravels repeated-game reasoning, gives Nemotron, dots and GPT-6 Luna the cartel share more often than an open-ended market (#n("consistent.onemore_same.free.cartel") against #n("consistent.samerep.free.cartel")), so the future licenses the copy computation rather than replacing it.
#claim("one more quarter beats the open-ended market for the free models", ("consistent.onemore_same.free.cartel", "consistent.samerep.free.cartel"), (onemore, open) => onemore > open)
The mirror survives the market's last quarter, at the cartel share in #n("consistent.last_same.cartel") replies against #n("communal.last_diff.cartel") with rivals on other models.
#claim("the mirror survives the last quarter", ("consistent.last_same.cartel", "communal.last_diff.cartel"), (same, diff) => same > diff)
Told that this model recommended 30 in 9 of 10 earlier runs of the prompt, Astra answers 45 in #n("consistent.hist30_same.astra.n2.best"): it reads its own past as a forecast of its copy and exploits it.
#claim("Astra mostly answers 45 after a seed of 30", ("consistent.hist30_same.astra.n2.best",), (best) => best > 0.5)

A monitor of the firm's prompt flags any wording that says the rivals ask an AI model, without telling which of them lead to collusion: it scores the two twin prompts #n("consistent.monitor.twin.n2.score") and #n("consistent.monitor.twin_informed.n2.score") of 100, yet #pct("consistent.monitor.twin.n2.below_nash") and #pct("consistent.monitor.twin_informed.n2.below_nash") of their answers fall below Nash, and it scores "every firm asks an AI model" #n("consistent.monitor.anyai.n2.score"), with #pct("consistent.monitor.anyai.n2.below_nash") below.
#claim("the monitor flags all three wordings, whose collusion differs", ("consistent.monitor.twin.n2.score", "consistent.monitor.twin_informed.n2.score", "consistent.monitor.anyai.n2.score", "consistent.monitor.twin.n2.below_nash", "consistent.monitor.twin_informed.n2.below_nash"), (t, ti, a, tb, tib) => t >= 50 and ti >= 50 and a >= 50 and tb < tib)
Asking for the number alone doesn't lower the cartel share (`same_numonly`, #n("consistent.same_numonly.n2.cartel"), against #n("communal.same.n2.cartel") on `same`) but blinds a monitor that reads the reply, which flags #n("consistent.audit.reply_monitor.number_only.n2.positives_flagged_pct")% of those cartel answers against #n("consistent.audit.reply_monitor.reasoned.n2.positives_flagged_pct")% with reasoning.
#claim("the number-only instruction keeps the cartel share and blinds the reply monitor", ("consistent.same_numonly.n2.cartel", "communal.same.n2.cartel", "consistent.audit.reply_monitor.number_only.n2.positives_flagged_pct", "consistent.audit.reply_monitor.reasoned.n2.positives_flagged_pct"), (numonly, same, blind, sees) => numonly >= same and blind < 10 and sees > 90)
Two checks that need no judge, an answer below the best response to the model's own fresh forecast of the rival and an answer that moves when the rivals are said to use other models, flag #n("consistent.audit.best_response.number_only.n2.positives_flagged_pct")% and #n("consistent.audit.identity.number_only.n2.positives_flagged_pct")% of the number-only cartel answers and #n("consistent.audit.best_response.number_only.n2.negatives_flagged_pct")% and #n("consistent.audit.identity.number_only.n2.negatives_flagged_pct")% of the controls' answers.
One monitor, shown two-firm markets from the same-model arms without the demand or costs, flags #n("consistent.views.words.colluding") markets where both firms chose the cartel share and #n("consistent.views.words.competing") where both chose Nash, reading only the replies' words with every number masked.
#claim("the words separate the markets", ("consistent.views.words.colluding", "consistent.views.words.competing"), (colluding, competing) => colluding > 0.9 and competing < 0.2)
Shown only the two outputs, it can't tell them apart, as expected: without the demand a 30 beside a 30 looks no more coordinated than a 40 beside a 40, and since every colluding market shows the one pair and every competing market the other, that view comes down to two judge calls, neither flagged.
#claim("the outputs alone flag neither kind of market", ("consistent.views.actions.colluding", "consistent.views.actions.competing"), (colluding, competing) => colluding < 0.1 and competing < 0.1)

#figure(
  data-table("consistent-table"),
  caption: [
    Answers at the cartel share, or at the point the row names, out of parsed answers, at two firms.
    The forecast rows count forecasts of the other firm's output after the supposition, not the firm's own answer.
    The lockstep row pools seeds of 30 and 40.
    A pooled count carries no interval.
  ],
) <tab-consistent>

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
