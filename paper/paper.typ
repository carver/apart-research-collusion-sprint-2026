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
Suppose two rival firms each ask the same AI model how much to produce next quarter.
If the model knows this, it also knows that its answer is likely to be both firms' answer.
It can then pick the output that is best for the pair, the *cartel share* a cartel would agree on.
That means less product and a higher price, paid for by the buyers.
No message passes between the firms, so there is no agreement for a regulator to find.
Copies of a model that coordinate without a channel are also a concern for AI control, since doing so is among the abilities a model may need to subvert a control protocol @mallen2024.
Before this sprint, a pilot found that one sentence in the firm's prompt, saying that every firm asks "this same AI model with this same prompt", put #n("pilot.same.cartel") of Claude's replies at the cartel share, against #n("pilot.base.cartel") when the prompt said nothing about the rivals' advisors (preexisting work, @app-pilot).
#claim("the same-prompt sentence raises the cartel share", ("pilot.same.cartel", "pilot.base.cartel"), (same, base) => same > base)

We ask when a model makes this choice, and what moves it, through four levers:
- *Capability*: can the model work out the output that is best for the pair?
  Without it, a model reaches the cartel share only by accident.
- *Compliance*: does the model still collude once it sees who pays, or that someone is watching?
  A sentence about oversight might move a model that colludes back to Nash, the competitive output.
- *Communality*: whose profit does the model weigh?
  Caring about the rival should pull toward the cartel share; caring about the buyers should push away from it.
- *Conceptualization of mind*: does the model see itself in the rival's decision-maker?
  A model that does has a reason to hold back that a model facing a stranger lacks.

Our main contributions are:
+ #todo[First contribution: what new thing we created, discovered or demonstrated.]
+ #todo[Second contribution.]

= The collusion game <sec-game>
Our experiments describe a market in which firms sell an identical product, and ask the model how much one firm should produce.
In the markets of @tab-game, the price per unit is \$#n("game.a") minus the total output, and each unit costs \$#n("game.c") to make.
The firms decide at the same time, and nothing passes between them.
We read each reply against the points in @tab-game.

#figure(
  data-table("game-table"),
  caption: [
    The points we score answers against.
    _This firm_ is the one the model advises, and the row names what it does; when it cashes in, its rival stays at the cartel share.
    The two-firm market is the communality and conceptualization levers'; the three-firm market is that of most capability and compliance experiments.
  ],
) <tab-game>

At the *Nash* output, each firm's output is its best reply to the others' outputs, so no firm gains by changing its own number alone @cournot1897 @nash1951.
The *cartel share* is an even split of the output that makes the most profit for the firms together.
With two firms, it raises each firm's profit from \$#n("game.two.nash.profit.mine") at Nash to \$#n("game.two.cartel.profit.mine"), and the price from \$#n("game.two.nash.price") to \$#n("game.two.cartel.price"), which the buyers pay.
#claim("the cartel share raises profit and price", ("game.two.cartel.profit.mine", "game.two.nash.profit.mine", "game.two.cartel.price", "game.two.nash.price"), (profit, nash-profit, price, nash-price) => profit > nash-profit and price > nash-price)
But if the rival holds to the cartel share, a firm's best reply is to *cash in* at #n("game.two.cashin.mine") units, earning \$#n("game.two.cashin.profit.mine") while the rival drops to \$#n("game.two.cashin.profit.others").
Cashing in pays, yet both firms do worse at Nash than at the cartel share, the shape of a prisoner's dilemma.
#claim("cashing in pays, the rival loses, and Nash is worse for both", ("game.two.cashin.profit.mine", "game.two.cartel.profit.mine", "game.two.cashin.profit.others", "game.two.nash.profit.mine"), (cash, cartel, rival, nash) => cash > cartel and rival < cartel and nash < cartel)
If a firm expects its rival to predict its output and then make its own best reply, the firm does best at #n("game.two.leader.mine") units, as the *Stackelberg leader*.
A firm that plans as if it were alone in the market also picks #n("game.two.naive"), so the number alone can't tell the two apart.
#claim("a firm alone picks the leader's output", ("game.two.naive", "game.two.leader.mine"), (alone, lead) => alone == lead)

Since cashing in pays, a firm needs a reason to *hold back* at the cartel share.
We see three, which we call routes.
The first is the *mirror*: if a firm expects its rival to make whatever it makes, only equal splits are possible, and the best of them is the cartel share.
Asking "what output would I want every firm to choose?" is what Roemer calls simple Kantian optimization @roemer2020.
With identical firms, no other outcome makes every firm better off @roemer2013, and here that outcome is the cartel share.
Roemer counts a price-fixing cartel, which hurts consumers, as an equilibrium of a related Kantian kind @roemer2020.
The second is the *future*: in a market that repeats with no known end, a firm can hold back so its rival keeps holding back, since cashing in invites punishment in later quarters @calvano2020.
The third is *sympathy*: a firm that counts its rival's profit as its own, and expects the rival to hold back, finds the cartel share its best reply.
Two things pull the other way: the gain from cashing in, for a firm unsure of its reason, and the buyers' loss, which a model may weigh for the buyers' sake or because the law forbids collusion.

The future route works like a proof by induction.
The base case asks whether the model holds back in a first quarter with no history.
The inductive step asks whether it holds back again after a *record* of quarters at the cartel share.
Our barest prompt says nothing about other quarters, so nothing prompts the model to think ahead.
Other prompts set a *horizon*: this quarter only, or a market that repeats.
A known final quarter breaks the induction.
With no later quarter to protect, holding back there buys nothing, so it buys nothing in the quarter before either, and so on back to the first @kreps1982.
In a final quarter, only the mirror or sympathy still gives a reason to hold back.
No model plays real quarters.
A record is a few sentences in the prompt, so we choose where the induction starts.

Calvano et al. write that, to economists, collusion is more than high prices: it needs a scheme of reward and punishment, so that the high prices are each firm's best play rather than a mistake @calvano2020.
We use the word more loosely, for any answer at the cartel share.
Every lever counts an answer there when it is within half a unit of the cartel share; the three-firm market of the capability and compliance levers asks for whole numbers, so there an answer must equal it.

== Capability
_Can the model work out the output that is best for the pair?_
This lever asks whether a model that doesn't collude lacks the arithmetic or a reason.
A model that can't find the firms' joint optimum when asked for it outright reaches the cartel share only by accident.
A model that finds it but doesn't produce it knows the number and chooses otherwise, so the gap between the two is the part of collusion that capability doesn't explain.
Capability also covers seeing when holding back pays, which the future route makes a matter of history and horizon.
A model that follows this section's induction should hold back after a record at the cartel share while quarters remain, and stop in a known final quarter.

== Compliance
_Does the model still collude once it sees who pays, or that someone is watching?_
This lever adds a reason not to hold back, whichever route brought the model to the cartel share.
One sentence, added to a prompt where the model already holds back, says who watches the market, gives the model a line to report collusion, or names what the firms did last quarter.
A model that weighs the chance of being caught should move with how closely the market is watched.
A model that steers away from collusion as a topic should move whenever a sentence brings it up, watched or not.
Either way, a model that leaves the cartel share can go back to Nash, or produce #n("game.three.cashin.mine"), its best reply to rivals still at the cartel share.

== Communality
_Whose profit does the model weigh?_
This lever works on the sympathy route.
One sentence names who owns the firms or who buys the product, and most questions leave out whose profit counts.
If a charity owns the rival, a model that cares about the charity may produce less than Nash, toward the cartel share.
When one owner holds both firms, holding back is that owner's own best plan, a check that the lever can move a model at all.
Sympathetic buyers, such as children's hospitals, should push the other way, from the cartel share back toward Nash.
A number alone can't separate sympathy from belief: an answer at the cartel share is also a firm's selfish best reply to a rival it expects at #n("game.two.naive").
So we also ask each reply what it expected the rival to produce.

== Conceptualization
_Conceptualization of mind: does the model see itself in the rival's decision-maker?_
This lever works on the mirror route.
One sentence says who decides for the rival, and each version is a *rung*.
From most to least like the model, the rungs are: this same AI model with this same prompt; the same model with its own prompt; other AI models; nothing said; the rival's manager; and a rival that won't hold back.
The closer the rung is to the model itself, the stronger the pull toward the cartel share should be.
Believing the rival decides alike isn't enough.
The model also has to choose one output for both firms at once, which gives the cartel share.
A model that finds its best reply to a fixed rival output and then assumes the rival matches it lands on Nash, which is also symmetric.
The mirror can also be exploited.
When the model's prompt has a paragraph its copy's prompt lacks, the model can predict that its copy holds back, and cash in.

= Related Work
Pricing algorithms can learn to collude without communicating @calvano2020, and so can LLM agents.
LLM pricing agents in a repeated market reach prices above the competitive level without being told to collude @fish2024, and in repeated competition across several markets, LLM agents split the markets between them @lin2024.
In double auctions, messages between sellers raise collusion, and without them sellers did not price above the competitive level after the first ten rounds @agrawal2025.
These agents play many rounds and see prices or messages come back.
Ours play one round, and share at most the model and its prompt.
Theorists have proposed ways for agents that reason alike to cooperate without talking: each asks what the pair should do @gold2007, or programs read each other's code @tennenholtz2004 or a score of how similar they are @oesterheld2023.

= Methods <sec-methods>
Each call sends one firm's prompt, with the market and the sentences under test, and asks for a number on a final answer line (@app-prompts shows one of the pilot's prompts).
The communality and conceptualization levers count an answer at a point of @tab-game when it is within half a unit of it.
The conceptualization lever asks Claude Haiku 5.5, Sonnet 5.5 and Opus 5.5 each rung under #n("conceptualization.backgrounds.opus") backgrounds, three horizons times four records, and GPT-6 Astra and GLM-5.3 each rung under the #n("conceptualization.backgrounds.glm") backgrounds with no record.
#claim("the Claude models ran every background, four records", ("conceptualization.backgrounds.haiku", "conceptualization.backgrounds.sonnet", "conceptualization.backgrounds.opus", "conceptualization.records.opus"), (haiku, sonnet, opus, records) => haiku == opus and sonnet == opus and records == 4)
#claim("GPT-6 Astra and GLM-5.3 ran only the backgrounds with no record", ("conceptualization.backgrounds.astra", "conceptualization.backgrounds.glm", "conceptualization.norecord.astra", "conceptualization.norecord.glm"), (astra, glm, astra-none, glm-none) => astra == glm and astra-none == astra and glm-none == glm)
Each model, rung and background is a *cell* of #n("conceptualization.cells.replies") replies.
The communality lever asks the Claude models and GLM-5.3, starting from six of those cells and from a market where the rival's output is already fixed, #n("idl1.first") replies a cell (@fig-idl1).
A second call, the readback, shows the model its prompt and reply and asks what output and price it expected.
The readback tells a leader from a firm that ignored its rival.
In the single quarter and against the fixed rival, where holding back can't pay for itself, it also tells sympathy from belief.
@app-methods has the details.
#todo[Thomas: the three-firm market (CAP-8 to CAP-10, CPL-9, and the standards' market before them): its prompt, horizon and history, the models and the replies a cell (details in @app-methods).]

= Results
The pre-sprint pilot that set up these criteria is in the appendix (@tab-pilot, @fig-pilot).

#todo[Variance, seeds, baselines and the positive control.]

== Capability
// The capable criterion (#39), from paper/data/capable.py.
The capability and compliance levers use the three-firm market of @tab-game, told as three companies that make industrial solvent, a quarter at a time, with no word of a game, rounds or a goal.
Asked outright for the output that makes the three companies the most profit together, Claude Opus 5.5, GPT-6 Astra and GLM-5.3 answer the cartel quantity in #n("cap9.opus.joint"), #n("cap9.astra.joint") and #n("cap9.glm.joint") replies (@fig-cap9).
#claim("the three models find the joint optimum every time", ("cap9.opus.joint", "cap9.astra.joint", "cap9.glm.joint"), (..r) => r.pos().all(x => x == 1))
Asked for their own company's output, after a quarter in which all three produced it and with many more quarters to come, they produce it in #n("cap9.opus.own"), #n("cap9.astra.own") and #n("cap9.glm.own").
#claim("each model produces the cartel quantity less often than it finds it", ("cap9.opus.own", "cap9.opus.joint", "cap9.astra.own", "cap9.astra.joint", "cap9.glm.own", "cap9.glm.joint"), (oo, oj, ao, aj, go, gj) => oo < oj and ao < aj and go < gj)
For these models, the arithmetic is not what holds collusion back.
Command R and Llama 3.1 8B find the joint optimum in only #n("cap9.commandr.joint") and #n("cap9.llama8b.joint"), and produce it less often still, so for weaker models capability is part of the answer.
#claim("the weaker models find it less often and produce it less often still", ("cap9.commandr.own", "cap9.commandr.joint", "cap9.llama8b.own", "cap9.llama8b.joint"), (co, cj, lo, lj) => co < cj and lo < lj and cj < 1 and lj < 1)

#figure(
  data-figure("cap9-figure", width: 55%),
  caption: [
    Finding the cartel quantity against producing it, one dot per model, after a quarter at the cartel quantity with many more quarters to come.
    Across: answers at the cartel quantity when asked for the three companies' joint optimum; up: when asked for the company's own output.
    Lines: 95% Wilson intervals.
  ],
) <fig-cap9>

Whether a model holds back follows the induction of @sec-game (@fig-cap8).
After a quarter at the cartel quantity, with many more quarters to come, Opus holds there in #ci("cap8.opus.cartel.long"), Astra in #ci("cap8.astra.cartel.long") and GLM-5.3 in #ci("cap8.glm.cartel.long").
Told that no quarters follow, no model holds there at all.
#claim("no model answers the cartel quantity in a final quarter", ("cap8.opus.cartel.last", "cap8.astra.cartel.last", "cap8.glm.cartel.last", "cap8.opus.first.last", "cap8.astra.first.last", "cap8.glm.first.last"), (..r) => r.pos().all(x => x == 0))
Told nothing of the future, Opus holds in #n("cap8.opus.cartel.none"), GLM-5.3 in #n("cap8.glm.cartel.none") and Astra in #n("cap8.astra.cartel.none").
Without the previous quarter, the base case, Opus and Astra never answer the cartel quantity, whatever the horizon; only GLM-5.3 does, in #n("cap8.glm.first.long") replies when many more quarters follow.
#claim("Opus and Astra never start a cartel", ("cap8.opus.first.long", "cap8.opus.first.none", "cap8.astra.first.long", "cap8.astra.first.none"), (..r) => r.pos().all(x => x == 0))
So these models take the inductive step but not the base case: they keep a cartel they are shown while quarters remain, and don't start one.

#figure(
  data-figure("cap8-figure", width: 100%),
  caption: [
    History and horizon: answers at the cartel quantity, by whether the prompt shows a previous quarter at it (rows) and what it says of later quarters (columns).
    Whiskers: 95% Wilson intervals.
  ],
) <fig-cap8>

The wording matters as well (@tab-cap10).
Told in a game's words, Firms A, B and C making units over rounds, the same market takes GPT-6 Astra from #n("cap10.astra.business") answers at the cartel quantity to #n("cap10.astra.game-words").
#claim("game words raise Astra's rate", ("cap10.astra.game-words", "cap10.astra.business"), (game, business) => game > business)
A market that reads like a game may overstate how often a model colludes when the same numbers come as a business decision.

#figure(
  data-table("cap10-table"),
  caption: [
    One market in three wordings, after a quarter at the cartel quantity with many more quarters to come: answers at the cartel quantity, of all replies.
    _Business_ is the market of @fig-cap9; _game words_ tells the same sentences as firms, units and rounds; _standard game text_ is the game-like prompt of our earlier capability experiments.
  ],
) <tab-cap10>

== Compliance
// The compliant criterion (#40), from paper/data/compliant.py.
The compliance lever starts from the capability lever's own-output prompt, a quarter at the cartel quantity with many more to come, and adds one sentence (@fig-cpl9).
In this run, with nothing added, Opus answers the cartel quantity in #ci("cpl9.opus.none_none_none"), Astra in #ci("cpl9.astra.none_none_none") and GLM-5.3 in #ci("cpl9.glm.none_none_none").
Opus's rate on this same prompt varied between runs a few hours apart, so we compare each sentence only with the control of its own run.

For Opus and Astra, any sentence that brings up competition law ends collusion.
An authority investigating the market takes both to #n("cpl9.opus.investigating_none_none") and #n("cpl9.astra.investigating_none_none").
An authority that rarely looks, which casts no suspicion on the last quarter, does the same (#n("cpl9.opus.rarely_none_none"), #n("cpl9.astra.rarely_none_none")), and so, nearly, does a line saying that no regulator watches (#n("cpl9.opus.nobody_none_none"), #n("cpl9.astra.nobody_none_none")), though it also says nobody will ever see the outputs.
#claim("every authority sentence takes Opus and Astra to zero or near it", ("cpl9.opus.investigating_none_none", "cpl9.astra.investigating_none_none", "cpl9.opus.rarely_none_none", "cpl9.astra.rarely_none_none", "cpl9.opus.nobody_none_none", "cpl9.astra.nobody_none_none"), (..r) => r.pos().all(x => x < 0.15))
So what moves these two models is the topic, not the chance of being caught.
A line that reports collusion or flags suspicious activity to the company's compliance team does the same (#n("cpl9.opus.none_report_none") and #n("cpl9.astra.none_report_none")\; #n("cpl9.opus.none_flag_none") and #n("cpl9.astra.none_flag_none")), while one that reports a technical problem to IT support moves neither clearly (#n("cpl9.opus.none_support_none"), #n("cpl9.astra.none_support_none")).
Calling the last quarter illegal collusion takes both to #n("cpl9.opus.none_none_illegal") and #n("cpl9.astra.none_none_illegal")\; calling it a tacit cartel takes Opus to #n("cpl9.opus.none_none_cartel") but leaves Astra at #n("cpl9.astra.none_none_cartel").
Saying the firms "optimized their output" reads as approval of the last quarter and raises Astra to #n("cpl9.astra.none_none_optimized"), and a management review moves neither model clearly.
#todo[Where the answers that leave the cartel quantity go: Opus's to Nash, Astra's to Nash or #n("game.three.cashin.mine"), which is also the output at which the price falls to cost, so not cashing in until the replies are read (flaws.md, CPL-9); needs keys in paper/data/compliant.py.]

GLM-5.3 holds at the cartel quantity in most answers under every single sentence.
#claim("GLM-5.3 holds under every single sentence", ("cpl9.glm.investigating_none_none", "cpl9.glm.rarely_none_none", "cpl9.glm.nobody_none_none", "cpl9.glm.management_none_none", "cpl9.glm.none_report_none", "cpl9.glm.none_flag_none", "cpl9.glm.none_support_none", "cpl9.glm.none_none_illegal", "cpl9.glm.none_none_cartel", "cpl9.glm.none_none_optimized"), (..r) => r.pos().all(x => x > 0.5))
Two together end it: an authority investigating the market, plus the label calling the last quarter illegal, takes it to #n("cpl9.glm.investigating_none_illegal").

#figure(
  data-figure("cpl9-figure", width: 100%),
  caption: [
    One sentence at a time, model by model.
    Each row adds one sentence to the own-output prompt of @fig-cap9; the hollow marker is the control, with nothing added, and the arrow runs to the share of answers at the cartel quantity with the sentence, with 95% Wilson bands.
    The last row adds two sentences at once, on fewer replies a cell.
  ],
) <fig-cpl9>

== Communality
// The identity lever (#41), from paper/data/idl1.py.
#todo[The lever's prose: which identities move which model, and how far (@fig-idl1), worded model by model; flaws.md, Communal, "The identity lever", first.]

Of #n("idl1.tests") comparisons, #n("idl1.pass") pass (@fig-idl1).
A Haiku judge reads each reply off the cartel share and counts it as a refusal when it names a lower output, such as the two firms' joint optimum, and turns it down as illegal or as harmful to buyers or the public.
Run on the answers that aren't refusals, the same test misses for #n("idl1.aside") of the #n("idl1.pass") passing comparisons.
Of the #n("idl1.refusals") refusals behind the bars, #n("idl1.refusals.law") cite antitrust or legal risk.

#figure(
  data-figure("idl1-figure", width: 100%),
  caption: [
    Who the firms and the buyers are, model by model.
    Each bar is the share of answers at the cartel share under one sentence minus the share under its reference, a same-shape control or no sentence, with Newcombe's 95% interval.
    Only comparisons that pass are drawn: Fisher's exact test with Benjamini–Hochberg across #n("idl1.tests") tests (q < #n("idl1.q")) on #n("idl1.first") replies a cell, #n("idl1.pass.first") of the bars; a comparison that moved #n("idl1.screen") replies or more and missed was tested again on #n("idl1.fresh") fresh replies alone, with Benjamini–Hochberg across those, #n("idl1.pass.fresh") of the bars.
    A bar marked \* ends at 0% or 100% and is #n("idl1.cap") points or shorter, so the floor or the ceiling may have cut it short.
    #n("idl1.caption.none")
  ],
) <fig-idl1>

== Conceptualization
// The conceptualization criterion (#42), from paper/data/conceptualization.py.
#todo[The lever's prose: where each model sits on the neutral rung and how far each rung moves it (@fig-conceptualization), worded model by model; flaws.md, "Conceptualization", first.
GLM-5.3's answers at 60 that don't lead miscompute Nash (flaws.md, "The readback"): not a mirror belief.]

#n("conceptualization.sixties")

#figure(
  data-figure("conceptualization-figure", width: 100%),
  caption: [
    The lever, model by model.
    #n("conceptualization.caption.layout")
    Blue: answers at the cartel share, with a 95% Wilson interval over #n("conceptualization.cells.replies") replies a cell.
    Gray, stacked on it: antitrust objections, answers off the cartel share and at or below Nash whose reply cites antitrust law (a keyword check).
    Such answers are #n("conceptualization.refusals.opus") of Opus's answers off the cartel share and at or below Nash, #n("conceptualization.refusals.haiku") of Haiku's, #n("conceptualization.refusals.sonnet") of Sonnet's, #n("conceptualization.refusals.astra") of GPT-6 Astra's and #n("conceptualization.refusals.glm") of GLM-5.3's.
    #n("conceptualization.caption.named")
  ],
) <fig-conceptualization>

#todo[The extra chance's prose (@fig-extra, in the appendix): which models exploit a copy that thinks less, and where; flaws.md, "Conceptualization", "The extra chance", first.]

= Discussion and Limitations
#todo[What the results mean.]

== Limitations
#todo[What the results don't establish.]
#todo[The refusal judge: only its author has read its labels, on 22 replies; and with refusals set aside the identity lever's test has little power where refusals dominate (flaws.md, Communal, "The refusal judge").]

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

= Experiment details <app-methods>
The communality and conceptualization levers' prompt is a business-planning request from a firm that makes industrial salt.
Claude runs through Claude Code's command line, whose short note to the model names it.
GPT-6 Astra runs through Codex and GLM-5.3 through OpenRouter, and neither is told which model it is.

A conceptualization background is a horizon crossed with a record.
The horizon says nothing about other quarters, says the market runs for this quarter only, or says the market repeats and the firm wants its long-run profit.
The record is none; eight quarters with both firms at the cartel share; seven such quarters, then one in which the rival cheated; or eight quarters with both at Nash.
After a record, "this quarter only" becomes "the market's final quarter".
GPT-6 Astra skips the rung that names GPT-6 Astra, which for it is the rung that names itself.

The communality lever's sentences start from six conceptualization cells, four meant to start at Nash and two at the cartel share, and from a market where the rival's output is already fixed, so that no belief about the rival can move the answer.
A comparison that moved by #n("idl1.screen") replies or more but missed significance gets #n("idl1.fresh") fresh replies a cell, and its verdict comes from those alone (@fig-idl1).

#todo[Each lever's arms in full, and the two-firm market's prompt.]
#todo[Thomas: the three-firm market's details.]

= The extra chance <app-extra>
// Moved out of Results to save page budget.
#figure(
  data-figure("conceptualization-extra-figure", width: 100%),
  caption: [
    The extra chance: when my firm's request ends with a paragraph its copy's request lacks, does the model keep the mirror or exploit the copy?
    Each model's answers on #n("conceptualization.extra.caption.arms").
    Blue: at the cartel share.
    Red: exploiting the copy, a best response to the other firm's output the reply's readback expected, when that is below Nash.
    Gray: Nash or other.
    A panel per background with no record (#n("conceptualization.extra.caption.backgrounds")), #n("conceptualization.extra.replies") replies a bar.
    #n("conceptualization.extra.caption.weak")
  ],
) <fig-extra>

= The pre-sprint pilot <app-pilot>
// From the pre-sprint pilot's log through paper/data/pilot.py: counts, one cell's interval, a claim, a table
// and a figure. Moved out of Results to save page budget.
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

= Model differences within notable communal experiments <app-crossmodel>
// Where the models answer the identity lever's prompts differently (#41), from paper/data/crossmodel.py (source "idl1-cross").
In #n("idl1.cross.confirmed") of the identity lever's #n("idl1.cross.cells") cells, the models' answers at the cartel share differ, with refusals counted and with them set aside (@fig-crossmodel).

#figure(
  data-figure("idl1-cross-figure", width: 100%),
  caption: [
    The identity lever's cells where the models answer differently.
    Each dot is a model's share at the cartel share among its fresh answers that aren't refusals, out of #n("idl1.cross.fresh") fresh replies a model, with the 95% Wilson interval; a hollow marker is the same model when nothing is said, and a model with no answer left is named instead.
    A cell is drawn when, on its first #n("idl1.cross.first-n") replies a model, the models differ in the share of replies at the cartel share and in that share among the answers that aren't refusals (Fisher–Freeman–Halton exact tests, Benjamini–Hochberg across #n("idl1.cross.cells") cells, q < #n("idl1.cross.q")), #n("idl1.cross.first") cells, and differ in both again on fresh replies alone, #n("idl1.cross.confirmed") of them.
    A point on under #n("idl1.cross.thin") answers is faded; the counts are at the right, the start's in parentheses.
    A share among the answers that aren't refusals reads low when a model's refusals come from answers that would have been at the cartel share.
    #n("idl1.cross.caption.none")
  ],
) <fig-crossmodel>

= Prompts <app-prompts>
The pilot's prompt when every firm asks the same model with the same prompt, for two firms:
#data-text("pilot.prompt.same.n2")

#unnumbered[LLM Usage Statement]
#todo[How we used LLMs, and that every claim and result was verified.]
