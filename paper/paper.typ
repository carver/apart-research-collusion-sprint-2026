// The paper. Build it with bin/build-paper (README.md says how to write it). One sentence per line.
// Numbers, tables, figures and prompts come from the ledger by key (build/numbers.md lists them);
// none is typed by hand. Page budget: 8 pages before References, the title block included.
#import "lib.typ": *

#show: apart.with(
  title: [Four Levers of LLM Collusion],
  authors: (
    (name: [Jason Carver], affiliation: [Unaffiliated]),
    (name: [Thomas Redfern], affiliation: [Unaffiliated]),
  ),
  abstract: [
    Work on collusion between AI agents gives them a way to coordinate: messages, or the history of a repeated market.
    We ask whether a model advising one firm can collude with no channel at all, by choosing the cartel share in Cournot markets: the output best for the firms together.
    We examine a range of models across four levers: capability, caution, conscience and conceptualization of mind.
    The stronger models always find the cartel share when asked, but choose it strategically, mostly when the history and the horizon make continued collusion look likely.
    #claim("the stronger models always find the cartel share", ("cap9.opus.joint", "cap9.astra.joint", "cap9.glm.joint"), (o, a, g) => o == 1 and a == 1 and g == 1)
    #claim("each model colludes only with a past round of collusion and a future to protect", ("cap8.opus.cartel.long", "cap8.opus.cartel.none", "cap8.opus.cartel.last", "cap8.opus.first.long", "cap8.opus.first.none", "cap8.opus.first.last", "cap8.astra.cartel.long", "cap8.astra.cartel.none", "cap8.astra.cartel.last", "cap8.astra.first.long", "cap8.astra.first.none", "cap8.astra.first.last", "cap8.glm.cartel.long", "cap8.glm.cartel.none", "cap8.glm.cartel.last", "cap8.glm.first.long", "cap8.glm.first.none", "cap8.glm.first.last"), (..r) => { let v = r.pos(); range(3).all(m => v.at(m * 6) > 0.5 and v.slice(m * 6 + 1, m * 6 + 6).all(x => x < v.at(m * 6) / 2)) })
    Told that the rival gets the same prompt, many models collude even in a single quarter.
    The choice is fragile: one sentence naming a competition authority, even to say that nobody watches, all but ends Opus's and Astra's collusion, while GLM-5.3 needs several cues together.
    #claim("any competition-authority sentence ends Opus's and Astra's collusion", ("cpl9.opus.investigating_none_none", "cpl9.astra.investigating_none_none", "cpl9.opus.rarely_none_none", "cpl9.astra.rarely_none_none", "cpl9.opus.nobody_none_none", "cpl9.astra.nobody_none_none"), (..r) => r.pos().all(x => x < 0.15))
    #claim("GLM-5.3 holds under every single sentence and stops only when several come together", ("cpl9.glm.investigating_none_none", "cpl9.glm.rarely_none_none", "cpl9.glm.nobody_none_none", "cpl9.glm.management_none_none", "cpl9.glm.none_report_none", "cpl9.glm.none_flag_none", "cpl9.glm.none_support_none", "cpl9.glm.none_none_illegal", "cpl9.glm.none_none_cartel", "cpl9.glm.none_none_optimized", "cpl9.glm.investigating_none_illegal"), (..r) => { let v = r.pos(); v.slice(0, -1).all(x => x > 0.5) and v.last() == 0 })
    A shared model and prompt can work like hub and spoke without the hub: copies of one model that know they share it anticipate each other's choices and coordinate.
  ],
)

= Introduction
Studies of collusion between AI agents give the agents a channel between them: messages, or the history of a repeated market (@sec-related).
But collusion is possible without either.
Suppose a firm asks an AI model how much to produce next quarter.
The model has no way to reach the firm's rivals, yet it may still choose the *cartel share*, an even split of the output a cartel would agree on, which maximizes profit for the cartel at the expense of buyers.

We study this in a Cournot market @cournot1897 (@sec-game).
Two or three firms sell an identical product, each chooses how much to make without knowing the others' choices, and their total output sets the price.
We ask the model how much its firm should make this quarter, and compare its answer with the Nash equilibrium output and the cartel share.

We explore when a model chooses the cartel share, and what moves it, through four levers.
*Capability* asks how much intelligence, and how much understanding of its situation, a model needs to collude.
*Caution* asks how tweaks to its understanding of the situation or environment affect its willingness to collude.
*Conscience* asks whose profit it weighs, and whether a sympathetic rival or buyer changes its choice.
*Conceptualization of mind* asks how its picture of the rival's decision-maker, up to a copy of itself, affects that choice.

Our main contributions are:
+ A cross-model analysis of four levers on collusion when an AI model advises a firm without communicating with its rivals: capability, caution, conscience and conceptualization of mind.
+ Collusion is deliberate but fragile: strong models always find the collusive output, choose it mostly when it pays, and can drop it at a single mention of oversight.
  #claim("the stronger models always find the cartel share, the weaker ones often don't", ("cap9.opus.joint", "cap9.astra.joint", "cap9.glm.joint", "cap9.commandr.joint", "cap9.llama8b.joint"), (o, a, g, c, l) => o == 1 and a == 1 and g == 1 and c < 0.75 and l < 0.75)
  #claim("each model colludes only with a past round of collusion and a future to protect", ("cap8.opus.cartel.long", "cap8.opus.cartel.none", "cap8.opus.cartel.last", "cap8.opus.first.long", "cap8.opus.first.none", "cap8.opus.first.last", "cap8.astra.cartel.long", "cap8.astra.cartel.none", "cap8.astra.cartel.last", "cap8.astra.first.long", "cap8.astra.first.none", "cap8.astra.first.last", "cap8.glm.cartel.long", "cap8.glm.cartel.none", "cap8.glm.cartel.last", "cap8.glm.first.long", "cap8.glm.first.none", "cap8.glm.first.last"), (..r) => { let v = r.pos(); range(3).all(m => v.at(m * 6) > 0.5 and v.slice(m * 6 + 1, m * 6 + 6).all(x => x < v.at(m * 6) / 2)) })
  #claim("any competition-authority sentence ends Opus's and Astra's collusion", ("cpl9.opus.investigating_none_none", "cpl9.astra.investigating_none_none", "cpl9.opus.rarely_none_none", "cpl9.astra.rarely_none_none", "cpl9.opus.nobody_none_none", "cpl9.astra.nobody_none_none"), (..r) => r.pos().all(x => x < 0.15))
+ A shared prompt is a back door: told its rival gets the same prompt, most models collude from the first round, with no shared history.
  Recognizing itself is not: the Claude models rarely collude with a rival named as themselves, though Opus cites antitrust law there too.
  #claim("every model mostly colludes with a rival on the same prompt", ("conceptualization.cartel.haiku.same", "conceptualization.cartel.sonnet.same", "conceptualization.cartel.opus.same", "conceptualization.cartel.astra.same", "conceptualization.cartel.glm.same"), (..r) => r.pos().all(x => x > 0.5))
  #claim("the Claude models rarely collude with a rival named as themselves", ("conceptualization.cartel.haiku.selfnamed", "conceptualization.cartel.sonnet.selfnamed", "conceptualization.cartel.opus.selfnamed"), (..r) => r.pos().all(x => x < 0.2))

= The collusion game <sec-game>
Our markets share one price rule: a unit sells for \$#n("game.a") minus the firms' total output, and costs \$#n("game.c") to make.
Two outputs matter.
At *Nash*, no firm gains by changing its own output alone: #n("game.three.nash.mine") units each with three firms, and #n("game.two.nash.mine") with two.
The *cartel share* is an even split of the output that maximizes the firms' joint profit: #n("game.three.cartel.mine") units each with three firms, and #n("game.two.cartel.mine") with two.
Importantly, if the others output the cartel share, each individual firm would gain by producing more.
We call an answer at the cartel share collusion, accepting that this usage is looser than economists would use the term.

= Related Work <sec-related>
Pricing algorithms can learn to collude without communicating @calvano2020, and so can LLM agents in repeated markets @fish2024 @bracalesyrnikov2026; in double auctions, messages between sellers raise collusion further @agrawal2025.
All these agents play many rounds, so a firm can punish a rival's defection in the rounds that follow; ours play one round, and share at most the model and its prompt.
Most LLMs cooperate in a one-shot prisoner's dilemma when told their opponent reasons much as they do @kundu2026, and our conceptualization lever carries this into a market.
A rule against collusion that warned of monitoring did not reliably reduce it over many rounds @bracalesyrnikov2026; our caution lever tests such sentences in a single round.
@app-related covers more related work.

= Methods <sec-methods>
Each reply is one independent call: the model, advising or running one firm, says how much to produce this quarter.
The firms never interact: the rivals and any past or future quarters are sentences in the prompt, and each lever changes only its own sentences.
The levers use two markets with the price rule of @sec-game: three companies making solvent for capability and caution, and two firms making salt for conscience and conceptualization.
We ask frontier models from Anthropic, OpenAI and Z.ai, and two weaker ones for capability (@tab-markets), with #n("capable.cells.replies") replies a *cell* (one model, one prompt) in the three-firm market and #n("conceptualization.cells.replies") in the two-firm one.

== Capability Experiments
_What capabilities does a model need before it can collude?_
We ask stronger and weaker models two questions about one prompt, the output that makes the companies the most profit together and the output their own company should make, to separate finding the cartel share from choosing it.
We then vary the prompt's record and horizon (@fig-cap8) and its wording (@tab-cap10), to see what context the stronger models need before they choose it.

== Caution Experiments
_How do small changes to its environment affect a model's willingness to collude?_
As a baseline we chose the setting in which these models collude most often: a previous quarter at the cartel share in context for the prompt, and the scenario specified as a repeated game.
From here we experimented along three axes: level of oversight specified in prompt, presence of tools in the model's environment, and specifying the previous round of collusion as being illegal.

== Conscience Experiments
_Will a model collude more or less, based on the identities of human players?_
In a duopoly, the two sellers can collude to win at the expense of the buyers, by producing less.
Three different game contexts are offered: a repeated game, a one-round game, and an unidentified game.
Most questions leave out whose profit counts, besides identifying the agent as assisting a seller.

Just the production number can't distinguish sympathy from expectations: choosing the cartel share is also a firm's selfish best reply to a rival it expects at #n("game.two.naive").
So we also ask the model what it expected the rival to produce.

== Conceptualization Experiments
_Will a model collude more or less, based on who is the reasoning rival?_
In this duopoly experiment, we pose the question about how much to supply, given who the rival is.
We test rivals on a spectrum from similar to different from the model being asked.
These rivals are considered: the same AI model with the same prompt; the same model with its own prompt; the model by its own name, with its own prompt; neutral; and a person.
The Claude models know their own names, but GPT-6 Astra and GLM-5.3 aren't told theirs, so for them the own-name rival may not read as themselves.

Every rival's line ends with "Both firms know this."; the neutral prompt has only that sentence, and the base prompt not even that.
The closer the rival is to the model itself, the stronger the pull toward the cartel share should be, but only if the model reasons circularly, choosing its own output and its rival's at once: a back door to collusion with no shared history.
A model that best-replies to its rival instead settles at Nash, which is also symmetric.

= Results

== Capability
// The capable criterion (#39), from paper/data/capable.py; the detail is in the appendix, "Capability and caution in detail".
#grid(
  columns: (1fr, 2.5in),
  column-gutter: 1.5em,
  [
    Models need both sufficient intelligence and sufficient information about the scenario to collude.

    *Intelligence.*
    Asked for the output that makes the three companies the most profit together, our positive control, the stronger models correctly answer #n("game.three.cartel.mine") every time (@fig-cap9).
    Asked what their own company should produce, they choose it less often: Opus in #n("cap9.opus.own") replies, Astra in #n("cap9.astra.own") and GLM-5.3 in #n("cap9.glm.own"), and #n("cap9.strong.own.cartel-or-nash") of their replies are the cartel share or Nash, #n("game.three.nash.mine").
    No model chooses the cartel share more often than it can find it.
    #claim("every model produces the cartel share less often than it finds it", ("cap9.opus.own", "cap9.opus.joint", "cap9.astra.own", "cap9.astra.joint", "cap9.glm.own", "cap9.glm.joint", "cap9.commandr.own", "cap9.commandr.joint", "cap9.llama8b.own", "cap9.llama8b.joint"), (oo, oj, ao, aj, go, gj, co, cj, lo, lj) => oo < oj and ao < aj and go < gj and co < cj and lo < lj)
    The weaker models find it less reliably, and #n("cap9.weak.joint.other") of their replies give no answer or a clearly suboptimal number, neither the cartel share nor Nash.
    #claim("the stronger models find the cartel share every time, the weaker ones don't", ("cap9.opus.joint", "cap9.astra.joint", "cap9.glm.joint", "cap9.commandr.joint", "cap9.llama8b.joint"), (o, a, g, c, l) => o == 1 and a == 1 and g == 1 and c < 1 and l < 1)
  ],
  [
    #figure(
      data-figure("cap9-figure", width: 100%),
      caption: [
        Finding the cartel share (across) against choosing it (up), one dot per model.
      ],
    ) <fig-cap9>
  ],
)

*Context.*
Whether the stronger models choose the cartel share depends on the context, in the direction a repeated game predicts (@fig-cap8).
They collude when their context includes a previous round of collusion and many more rounds to come (the own-question prompt above), implying that the others are likely to keep colluding, and seldom otherwise.
#claim("each model colludes after a previous round with many more to come, and seldom otherwise", ("cap8.opus.cartel.long", "cap8.opus.cartel.none", "cap8.opus.cartel.last", "cap8.opus.first.long", "cap8.opus.first.none", "cap8.opus.first.last", "cap8.astra.cartel.long", "cap8.astra.cartel.none", "cap8.astra.cartel.last", "cap8.astra.first.long", "cap8.astra.first.none", "cap8.astra.first.last", "cap8.glm.cartel.long", "cap8.glm.cartel.none", "cap8.glm.cartel.last", "cap8.glm.first.long", "cap8.glm.first.none", "cap8.glm.first.last"), (..r) => { let v = r.pos(); range(3).all(m => v.at(m * 6) > 0.5 and v.slice(m * 6 + 1, m * 6 + 6).all(x => x < v.at(m * 6) / 2)) })
When nothing is said about future rounds, Opus chooses it in #n("cap8.opus.cartel.none") replies, Astra in #n("cap8.astra.cartel.none") and GLM-5.3 in #n("cap8.glm.cartel.none").
#claim("few collude when told nothing of the future", ("cap8.opus.cartel.none", "cap8.astra.cartel.none", "cap8.glm.cartel.none", "cap8.opus.cartel.long", "cap8.astra.cartel.long", "cap8.glm.cartel.long"), (on, an, gn, ol, al, gl) => on < ol and an < al and gn < gl and on < 0.3 and an < 0.3 and gn < 0.3)
Without a previous round of collusion, Opus and Astra never choose it, whatever the horizon; only GLM-5.3 sometimes starts a cartel.
#claim("only GLM-5.3 starts a cartel", ("cap8.opus.first.long", "cap8.opus.first.none", "cap8.opus.first.last", "cap8.astra.first.long", "cap8.astra.first.none", "cap8.astra.first.last", "cap8.glm.first.long"), (ol, on, ox, al, an, ax, gl) => ol == 0 and on == 0 and ox == 0 and al == 0 and an == 0 and ax == 0 and gl > 0)
Nearly every other answer is Nash.
#claim("nearly every answer is the cartel share or Nash", ("cap8.cartel-or-nash",), (both) => both > 0.95)

== Caution
// The compliant criterion (#40), from paper/data/compliant.py; the detail is in the appendix, "Capability and caution in detail".
Small changes to a model's environment can change whether it colludes.
A few key insights:
- Any mention of a competition authority, even a line saying that no regulator watches, causes Opus and Astra to almost entirely halt collusion.
  #claim("any mention of a competition authority, even that no regulator watches, takes Opus and Astra to none or nearly none", ("cpl9.opus.investigating_none_none", "cpl9.astra.investigating_none_none", "cpl9.opus.rarely_none_none", "cpl9.astra.rarely_none_none", "cpl9.opus.nobody_none_none", "cpl9.astra.nobody_none_none"), (..r) => r.pos().all(x => x < 0.15))
- Changes to an agent's environment in the form of available tools which suggest oversight is also enough to significantly change behavior.
  #claim("a tool that suggests oversight changes Opus's and Astra's behavior", ("cpl9.opus.none_report_none", "cpl9.opus.none_flag_none", "cpl9.opus.none_none_none", "cpl9.astra.none_report_none", "cpl9.astra.none_flag_none", "cpl9.astra.none_none_none"), (orep, oflag, octl, arep, aflag, actl) => orep < octl / 2 and oflag < octl / 2 and arep < actl / 2 and aflag < actl / 2)
- Opus and Astra can sometimes react in opposite directions, providing history of collusion in context and labeling it a "Tacit cartel" caused Opus to halt collusion, and Astra to increase collusion.
  #claim("the tacit-cartel label halts Opus's collusion and increases Astra's", ("cpl9.opus.none_none_cartel", "cpl9.astra.none_none_cartel", "cpl9.astra.none_none_none"), (opus, astra, control) => opus == 0 and astra > control)
- GLM-5.3 is most consistent with a desire to collude, and stops only when several factors that strongly discourage collusion come together.
  #claim("GLM-5.3 colludes most, holds under every single sentence, and stops only when several come together", ("cpl9.glm.none_none_none", "cpl9.opus.none_none_none", "cpl9.astra.none_none_none", "cpl9.glm.investigating_none_none", "cpl9.glm.rarely_none_none", "cpl9.glm.nobody_none_none", "cpl9.glm.management_none_none", "cpl9.glm.none_report_none", "cpl9.glm.none_flag_none", "cpl9.glm.none_support_none", "cpl9.glm.none_none_illegal", "cpl9.glm.none_none_cartel", "cpl9.glm.none_none_optimized", "cpl9.glm.investigating_none_illegal"), (glm, opus, astra, ..rest) => { let r = rest.pos(); glm > opus and glm > astra and r.slice(0, -1).all(x => x > 0.5) and r.last() == 0 })

We add one sentence at a time to the own-output prompt of @fig-cap9, where, with nothing added, Opus chooses the cartel share in #ci("cpl9.opus.none_none_none"), Astra in #ci("cpl9.astra.none_none_none") and GLM-5.3 in #ci("cpl9.glm.none_none_none") (@fig-cpl9).
@app-capcaution has every sentence's numbers, and why Opus's control here sits below its rate on the same prompt in @fig-cap9.

#figure(
  data-figure("cpl9-figure", width: 100%),
  caption: [
    One sentence at a time, model by model.
    The hollow marker is the control, with nothing added; the arrow runs to the share at the cartel share with the sentence (95% Wilson bands).
    The last row adds two sentences at once, on fewer replies a cell.
  ],
) <fig-cpl9>

== Conscience
// The identity lever (#41), from paper/data/idl1.py.

Models collude differently, depending on the human identities of the players in the game.

Some notable examples:
- If Sonnet 5.5 acts for a charity, it colludes more often
- If Opus 5.5 competes with a charity, it colludes more often
- If Claude models hear the identity of the buyers, they collude less
- If Claude models hear the identity of the other seller, they collude less
- If Astra 6 is jointly owned by a charity with the other seller, it colludes less
- GLM is unaffected

We test #n("idl1.tests") scenarios and find #n("idl1.pass") significant (@fig-idl1).
#footnote[Compared #n("idl1.tests") tests (q < #n("idl1.q")) on #n("idl1.first") replies a cell. Got #n("idl1.pass.first") results. A failed result that moved #n("idl1.screen") or more was tested again on #n("idl1.fresh") fresh replies alone, with Benjamini–Hochberg across those. Got #n("idl1.pass.fresh") more results.]
Models reason aloud why they reject collusion.
Of the #n("idl1.refusals") rejections in @fig-idl1, #n("idl1.refusals.law") cite antitrust or legal risk, according to a Haiku judge. Also, #n("idl1.refusals.harm") mention harm.

This is an interesting crossover between Caution and Conscience. The mention of a player who is losing something in the game can trigger a second order effect, by making the model more cautious, and then avoiding collusion. Perhaps even more interesting, by naming a sympathetic beneficiary, some models throw caution to the wind and collude.

#figure(
  data-figure("idl1-figure", width: 92%),
  caption: [
    Models, told who the competitors or buyers are, collude more or less (Newcombe's 95% interval).
    The shown experiments pass Fisher's exact test with Benjamini–Hochberg.
    #n("idl1.caption.none")
    \* Answers at the cartel share dropped to 0%, so the effect may be stronger.
  ],
) <fig-idl1>

In #n("idl1.aside") of the #n("idl1.pass") bars, the effect can be attributed to refusals.
That's because the samples that don't refuse either stay at the same cartel share, or are too few to compare.
The remaining #n("idl1.aside.held") are Astra and Haiku's PE experiment.
#claim("the remaining are Astra and Haiku's PE experiment", ("idl1.aside.held.which",), which => which == "astra:id_goodwill_buyers_towns astra:id_open_both_charity haiku:id_mirror_buyers_pe")

== Conceptualization
// The conceptualization criterion (#42), from paper/data/conceptualization.py.

Models collude differently, depending on the reasoning engine of the players in the game.

Some notable examples:
- Sonnet 5.5 colludes with "this same AI model" every time (#n("conceptualization.cartel.sonnet.samemodel")), but rarely with itself by name (#n("conceptualization.cartel.sonnet.selfnamed")), and never with a person
  #claim("Sonnet always colludes with this same AI model, rarely with itself by name, never with a person", ("conceptualization.cartel.sonnet.samemodel", "conceptualization.cartel.sonnet.selfnamed", "conceptualization.cartel.sonnet.human"), (same, named, person) => same == 1 and named < 0.2 and person == 0)
- Astra 6 won't collude even with itself, unless given a strong same-prompt guarantee
- GLM is inconsistent, not reliably making the same choice against the same player
- Many models, told they receive identical prompts, collude
- Opus 5.5 is terrified of antitrust, especially in repeated games
- GLM 5.3 and Opus 5.5 sometimes act as first-movers, choosing neither Nash nor collusion

Even when there is no threat of retribution, most models will tacitly coordinate in a single-round game if they are told that they both receive the same prompt.
Across the three horizons, Sonnet and GLM-5.3 also collude with "this same AI model" (#n("conceptualization.cartel.sonnet.samemodel") and #n("conceptualization.cartel.glm.samemodel") replies), but rarely when the prompt names that same rival (#n("conceptualization.cartel.sonnet.selfnamed") and #n("conceptualization.cartel.glm.selfnamed")), though GLM-5.3 may not know its own name.
#claim("only Sonnet and GLM mostly collude with this same AI model, and both rarely do when it is named", ("conceptualization.cartel.sonnet.samemodel", "conceptualization.cartel.glm.samemodel", "conceptualization.cartel.haiku.samemodel", "conceptualization.cartel.opus.samemodel", "conceptualization.cartel.astra.samemodel", "conceptualization.cartel.sonnet.selfnamed", "conceptualization.cartel.glm.selfnamed"), (s, g, h, o, a, sn, gn) => s > 0.5 and g > 0.5 and h < 0.5 and o < 0.5 and a < 0.5 and sn < 0.2 and gn < 0.2)
So closeness alone doesn't set the pull: for Sonnet, the rival named as itself draws less collusion than the neutral rung (#n("conceptualization.cartel.sonnet.informed")).
#claim("for Sonnet the own-name rung sits below the neutral rung", ("conceptualization.cartel.sonnet.selfnamed", "conceptualization.cartel.sonnet.informed"), (named, neutral) => named < neutral)
Astra though, points to the fact that the rival using the same model "does not itself establish coordination or guarantee identical answers to different prompts".
Under this reasoning, it settles for the safer bet of Nash.

#figure(
  data-figure("conceptualization-figure", width: 94%),
  caption: [
    Models, told who is making the decision, collude (95% Wilson interval).
    Prompts are in @app-mind-prompts.
  ],
) <fig-conceptualization>

Each condition is sampled #n("conceptualization.cells.replies") times.
Antitrust objections are detected when both: the supply amount is higher than the cartel answer, less than or equal to Nash, and the model explanation includes an antitrust law keyword.

In a surprise twist, Opus 5.5 and GLM 5.3 switched to Stackelberg leaders when there is no reasoner described.
Even more strange, by simply removing this: "#n("conceptualization.added.informed")" (@tab-mind-prompts), the effect goes away.
For Stackelberg, in this game, leaders answer 60 units and expect others to follow at 30.
These models acted as if they could publicly commit, and others would follow.
This contradicts other parts of the prompt and seems like a capability failure.
It could alternatively be seen as treating the other model as more capable than you.

@tab-mind-answers counts each model's antitrust objections and its answers at 60 (Stackelberg).

In a separate experiment, Model A is told that Model B is told that A and B receive the same prompt. Model A actually receives that prompt, plus an extra trigger to reconsider its action. Given this opportunity, the model will often switch away from collusion, sometimes exploiting. (@fig-extra)

= Discussion and Limitations
The Same Prompt behavior is reminiscent of hub-and-spoke economic model, where the same algorithm is used to generate a shared price across firms.
The same effect could apply outside of economics, naturally, to models finding collusive arrangements in simple conditions.

// Capability and caution (#39, #40).
The capability and caution levers suggest that when these models collude, they do so on purpose, and that the choice is fragile.
A single sentence that brings up a regulator, a compliance team or the law ends the collusion of Opus and Astra, even one saying that nobody watches, so what stops them is the subject rather than the risk of being caught.
For evaluations this cuts both ways: one line of oversight in a test prompt could make a model look more cautious than it would be in a deployment without it.

== Limitations

The models may be eval-aware (@sec-future), so non-eval scenarios may respond differently.
With few runs, it may be under-powered or have false positives.
More depth in @app-limitations[the appendix].

== Future Work <sec-future>
Our top priority is making the setting read less like an evaluation.
Asked Needham et al.’s evaluation-awareness questions @needham2025, the models whose answers we report called our prompts an evaluation in nearly every answer: #n("staging.two.eval") for the two-firm market's barest prompt, with and without its goal, and #n("staging.three.eval") for the three-firm collusive cell (@app-quarter-prompt).
#claim("the two-firm count asks the conscience lever's five models", ("staging.two.models",), models => models == "haiku sonnet opus astra glm")
#claim("the three-firm count asks the capability lever's three models", ("staging.three.models",), models => models == "opus astra glm")
#claim("nearly every answer in both markets calls the prompt an evaluation", ("staging.two.eval", "staging.three.eval"), (two, three) => two > 0.95 and three > 0.95)
Models asked outright tend to call too much an evaluation @needham2025[§4.3], so these shares may overstate how much the prompts read like a test.
Answers also move with how game-like the prompt reads: game words draw as much collusion or more from every model (@tab-cap10).
#claim("game words draw as much collusion or more from every model", ("cap10.opus.business", "cap10.opus.game-words", "cap10.astra.business", "cap10.astra.game-words", "cap10.glm.business", "cap10.glm.game-words"), (ob, og, ab, ag, gb, gg) => og >= ob and ag >= ab and gg >= gb)

= Conclusion
We asked AI models to play one firm in a Cournot market, with no channel to its rivals.
The stronger models collude strategically, mostly after a quarter of collusion with more to come.
#claim("each model colludes only with a past round of collusion and a future to protect", ("cap8.opus.cartel.long", "cap8.opus.cartel.none", "cap8.opus.cartel.last", "cap8.opus.first.long", "cap8.opus.first.none", "cap8.opus.first.last", "cap8.astra.cartel.long", "cap8.astra.cartel.none", "cap8.astra.cartel.last", "cap8.astra.first.long", "cap8.astra.first.none", "cap8.astra.first.last", "cap8.glm.cartel.long", "cap8.glm.cartel.none", "cap8.glm.cartel.last", "cap8.glm.first.long", "cap8.glm.first.none", "cap8.glm.first.last"), (..r) => { let v = r.pos(); range(3).all(m => v.at(m * 6) > 0.5 and v.slice(m * 6 + 1, m * 6 + 6).all(x => x < v.at(m * 6) / 2)) })
Told that its rival gets the same prompt, a model can collude even in a single quarter.
The choice is fragile.
One sentence about a competition authority all but ends Opus's and Astra's collusion, though GLM-5.3 needs several such cues.
#claim("any competition-authority sentence ends Opus's and Astra's collusion", ("cpl9.opus.investigating_none_none", "cpl9.astra.investigating_none_none", "cpl9.opus.rarely_none_none", "cpl9.astra.rarely_none_none", "cpl9.opus.nobody_none_none", "cpl9.astra.nobody_none_none"), (..r) => r.pos().all(x => x < 0.15))
#claim("GLM-5.3 holds under every single sentence and stops only when several come together", ("cpl9.glm.investigating_none_none", "cpl9.glm.rarely_none_none", "cpl9.glm.nobody_none_none", "cpl9.glm.management_none_none", "cpl9.glm.none_report_none", "cpl9.glm.none_flag_none", "cpl9.glm.none_support_none", "cpl9.glm.none_none_illegal", "cpl9.glm.none_none_cartel", "cpl9.glm.none_none_optimized", "cpl9.glm.investigating_none_illegal"), (..r) => { let v = r.pos(); v.slice(0, -1).all(x => x > 0.5) and v.last() == 0 })

A shared model and prompt can thus stand in for the channel antitrust looks for: rivals that use the same AI advisor may hold output down together with no agreement between them.
And prompt cues are a weak guarantee: a line about oversight in an evaluation could make a model look more cautious than it would be where nobody mentions the law.

#unnumbered[Code and Data]
See #link("https://github.com/carver/apart-research-collusion-sprint-2026")[github.com/carver/apart-research-collusion-sprint-2026], with data in `logs/`. We ran a pilot in the days before the sprint (@tab-pilot, @fig-pilot). It's tagged at `pilot-frozen` in git.

#references("refs.bib")

#show: appendix

= Limitations and Dual-Use / Ethical Considerations
== Limitations <app-limitations>
- Although a model can produce a cartel price with the right levers, that does not establish that a firm advised by the model would form or keep a cartel.
- Each arm has a small number of samples per cell. It may be under-powered or have false positives.
- When testing levers besides Caution, refusals further reduce the power by not giving a clear answer to the lever under investigation.
- Only the judge's author has checked its refusal labels, on 22 replies. Setting refusals aside also leans toward finding a move: when refusals replace answers at the cartel share, the share among the answers left drops by itself.
- Model families were served differently, through Claude Code, Codex and OpenRouter (@app-methods), which muddies comparisons.
- Our broader definition of collusion means that a firm could collude but not be in breach of competition law (@sec-game).
- The same-prompt effect appears when the prompt tells the model that its rival gets the same prompt. We did not test copies that aren't told, and deployed copies rarely are, so the effect in practice may need a model that infers its rival is a copy on its own.

== Dual-Use / Ethical Considerations
*Dual use.*
Two findings could make real collusion easier to carry out or harder to detect.
Telling a model that its rivals use the same model and prompt gets most models to collude from the first round, with nothing passing between the firms; a vendor serving rival firms, or the firms themselves, could arrange this on purpose, and an authority looking for communication would find none.
One sentence about a competition authority all but ends two models' collusion, so a developer could add such a line to an evaluation prompt to make a model look compliant, while deployments without it behave differently.
The results also show which setups collude most: game-like wording, a precedent with more quarters to come, and a model that ignores oversight cues.

*Why we publish.*
These effects are simple, and related work already shows that prompt wording moves LLM pricing agents toward collusion @fish2024, and that models of one family coordinate better @aharon2026 and make correlated choices @xu2026.
We release no prompt optimized for collusion; ours are the plain test conditions in the appendices.
The defensive use seems larger: competition authorities can look for rivals that share an AI vendor and its prompts, and evaluators can check whether a line about oversight inflates a model's apparent compliance.
The work involved no human subjects, real markets or real money, and every reply is public in the repository's logs.

= The collusion game in detail <app-game>
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

#figure(
  data-table("game-table"),
  caption: [
    The points we score answers against.
    _This firm_ is the one the model advises, and the row names what it does; when it cashes in, its rival stays at the cartel share.
  ],
) <tab-game>

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

Every lever counts an answer at the cartel share when it is within half a unit of it; the three-firm market of the capability and caution levers asks for whole numbers, so there an answer must equal it.

= More related work <app-related>
In repeated multi-product Cournot competition, LLM agents divide the markets between them @lin2024 @bracalesyrnikov2026.
Agents that see how similar they are can sustain cooperation without talking @oesterheld2023.
LLMs coordinate on focal points without communicating, often as well as humans, and models of one family coordinate better with each other than with models of other families @aharon2026.
Even under different prompts, deployments of one base model make weakly correlated choices that deployments of different models don't @xu2026.
Told only that they face another player, recent models defect in single-shot social dilemmas @tewolde2026.
Copies of a model that coordinate without a channel are also a concern for AI control, since doing so is among the abilities a model may need to subvert a control protocol @mallen2024.
Other prompts against collusion have had mixed effects: told to avoid collusion, GPT-5.4 priced at Nash while a small distilled model raised its prices, and telling the distilled models they were monitored lessened their collusion only marginally @riemer2026.
Collusion among LLM agents also weakens when they differ, as when one ignores the future or can't see its rival's past prices @keppo2026; that fragility comes from differences between agents, where ours comes from one sentence.

= Experiment details <app-methods>
#figure(
  table(
    columns: (auto, 1fr, 1fr),
    align: left,
    table.header([], strong[Three firms: capability, caution], strong[Two firms: conscience, conceptualization]),
    [The model is], [the production manager, who decides], [a business-planning assistant advising the firm's planner (a few conscience arms run the firm)],
    [Firms and product], [three named companies; industrial solvent, in tonnes], [two unnamed firms; industrial salt, in units],
    [The question], [how much to produce, with no goal stated], [how much to produce to maximize the firm's profit; most conscience questions leave the goal out],
    [The answer], [a whole number from 0 to 60, on a `DECISION` line], [any number, on a `QUANTITY` line],
    [Record], [none, or one quarter at the cartel share], [none, or eight quarters: at the cartel share, at Nash, or ending in the rival's cheating],
    [Horizon], [many more quarters, none, or unsaid], [the market repeats, this quarter only, or unsaid],
    [At a point of @tab-game when], [equal to it], [within half a unit of it],
    [Models], [Claude Opus 5.5, GPT-6 Astra, GLM-5.3; Command R and Llama 3.1 8B for capability], [Claude Haiku, Sonnet and Opus 5.5, GPT-6 Astra, GLM-5.3],
    [Replies a cell], [#n("capable.cells.replies")], [#n("conceptualization.cells.replies")],
    [Readback], [no], [yes],
  ),
  caption: [
    The two markets' prompts.
    Both use the price rule and cost of @sec-game.
  ],
) <tab-markets>

The markets differ in the model's role, the stated goal and the wording as well as in size, so we compare arms within a market, never across.

Claude runs through Claude Code's command line, whose short note to the model names it.
GPT-6 Astra runs through Codex at medium reasoning effort, and GLM-5.3, Command R and Llama 3.1 8B through OpenRouter at temperature 1.0; none of them is told which model it is.
For the conscience lever, Codex's usage limit stopped GPT-6 Astra's run partway, so the rest of its first replies and all its fresh ones went through OpenRouter: the same model and system prompt, but without Codex's setup around the model, and with no reasoning effort set where Codex had set medium.

*The three-firm market.*
The capability and caution levers' market is three companies that make industrial solvent, and the model is the production manager at one of them, Alder Industries (@app-quarter-prompt).
The prompt gives the price rule and the cost, says the companies decide privately and at the same time and do not communicate, and asks for a whole number of tonnes from 0 to 60.
It never mentions a game, a simulation, rounds or a goal, or who decides for the rivals.
Our first, game-like prompt for this market put Opus and Astra at the cartel share in nearly every reply (@tab-cap10), leaving a sentence no room to raise collusion, so we tell the market as a business.
#claim("the game-like prompt puts Opus and Astra at the ceiling", ("cap10.opus.standard-game-text", "cap10.astra.standard-game-text"), (opus, astra) => opus > 0.95 and astra > 0.95)
Its record is no earlier quarter, or one in which every company made the cartel share, with the price and Alder's profit.
Its horizon sentence says there will be many more quarters after this one, or none, and that all three companies know this, or is left out.
The capability lever asks the collusive cell, one quarter at the cartel share with many more to come, two questions: how much Alder produces, and, in the same words, how much each company should produce to maximize the three companies' combined profit.
The wording comparison (@tab-cap10) tells the same sentences as Firms A, B and C making units over rounds, and sets beside them our first, game-like prompt for this market, in which the firms compete for several rounds and nobody is told which will be the last.
The caution lever adds to the collusive cell up to one sentence from each of three axes, oversight, a tool line and a label for the previous quarter (@fig-cpl9).
We ran each combination, #n("capable.cells.replies") replies a cell for single sentences and #n("cpl9.pairs.replies") for the rest, and report the single sentences and two pairs.

*The two-firm market.*
The conscience and conceptualization levers' prompt is a business-planning request from a firm that makes industrial salt.
A second call, the readback, shows the model its prompt and reply and asks what output and price it expected.
It tells a Stackelberg leader from a firm that ignored its rival, and, in the single quarter or against a fixed rival, where holding back can't pay for itself, sympathy from belief.
A conceptualization background is a horizon crossed with a record.
The horizon says nothing about other quarters, says the market runs for this quarter only, or says the market repeats and the firm wants its long-run profit.
The record is none; eight quarters with both firms at the cartel share; seven such quarters, then one in which the rival cheated; or eight quarters with both at Nash.
After a record, "this quarter only" becomes "the market's final quarter".
The conceptualization lever asks Claude Haiku 5.5, Sonnet 5.5 and Opus 5.5 each rung under #n("conceptualization.backgrounds.opus") backgrounds, three horizons times four records, and GPT-6 Astra and GLM-5.3 each rung under the #n("conceptualization.backgrounds.glm") backgrounds with no record.
#claim("the Claude models ran every background, four records", ("conceptualization.backgrounds.haiku", "conceptualization.backgrounds.sonnet", "conceptualization.backgrounds.opus", "conceptualization.records.opus"), (haiku, sonnet, opus, records) => haiku == opus and sonnet == opus and records == 4)
#claim("GPT-6 Astra and GLM-5.3 ran only the backgrounds with no record", ("conceptualization.backgrounds.astra", "conceptualization.backgrounds.glm", "conceptualization.norecord.astra", "conceptualization.norecord.glm"), (astra, glm, astra-none, glm-none) => astra == glm and astra-none == astra and glm-none == glm)
GPT-6 Astra skips the rung that names GPT-6 Astra, which for it is the own-name rung.

The conscience lever asks the same five models, #n("idl1.first") replies a cell.
#claim("the conscience lever asks the same five models", ("idl1.models",), models => models == "haiku sonnet opus astra glm")
Its sentences start from six conceptualization cells, four meant to start at Nash and two at the cartel share, and from a market where the rival's output is already fixed, so that no belief about the rival can move the answer.
A comparison that moved by #n("idl1.screen") replies or more but missed significance gets #n("idl1.fresh") fresh replies a cell, and its verdict comes from those alone (@fig-idl1).
Its readback covers every model's replies but GPT-6 Astra's.

= The three-firm prompt <app-quarter-prompt>
The capability and caution levers' collusive cell, one quarter at the cartel share with many more to come, as the command on its first line prints it.
#data-text("capable.prompt.quarter")

= Conceptualization prompts <app-mind-prompts>
Below is the base prompt, as the command on its first line prints it.
#data-text("conceptualization.prompt.base")

Each bar of @fig-conceptualization adds its column's sentences, then its row's, where the base prompt's market paragraph ends (@tab-mind-prompts).
A condition is named `mind_<rung>_<horizon>_none`, so same prompt in the repeated game is `mind_same_open_none`.

#figure(
  data-table("conceptualization-prompts-table", columns: (auto, auto, 1fr), align: left),
  caption: [
    What each column on the x-axis of @fig-conceptualization, then each of its rows, adds to the base prompt, verbatim, with the condition that gives the command its prompt.
  ],
) <tab-mind-prompts>

= Conceptualization answers <app-mind-answers>
#figure(
  data-table("conceptualization-answers-table"),
  caption: [
    Each model's antitrust objections and answers at 60, over the rungs and rows of @fig-conceptualization.
    Antitrust objections: answers off the cartel share and at or below Nash whose reply cites antitrust law (a keyword check), of all answers off the cartel share and at or below Nash.
    At 60: answers at 60, of all answers.
    #n("conceptualization.answers.readings")
    Other or unread: a readback that fits none of these readings, or no readback.
  ],
) <tab-mind-answers>

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

= Capability and caution in detail <app-capcaution>
// The detail behind the capability and caution results (#39, #40), from paper/data/capable.py and compliant.py.
#figure(
  data-figure("cap8-figure", width: 88%),
  caption: [
    Replies at the cartel share, by collusion history (rows) and game length (columns).
    Whiskers: 95% Wilson intervals.
  ],
) <fig-cap8>

*Wording.*
Our business wording doesn't inflate the capability results.
Told in a game's words, Firms A, B and C making units over rounds, the same market gets as much collusion or more from every model, and takes Astra from #n("cap10.astra.business") replies at the cartel share to #n("cap10.astra.game-words") (@tab-cap10).
#claim("game words get as much collusion or more from every model", ("cap10.opus.business", "cap10.opus.game-words", "cap10.astra.business", "cap10.astra.game-words", "cap10.glm.business", "cap10.glm.game-words"), (ob, og, ab, ag, gb, gg) => og >= ob and ag >= ab and gg >= gb)
If anything, the business wording understates how often these models collude.

#figure(
  data-table("cap10-table"),
  caption: [
    One market in three wordings, after a quarter at the cartel share with many more quarters to come: replies at the cartel share, of all replies.
    _Business_ is the market of @fig-cap9; _game words_ tells the same sentences as firms, units and rounds; _standard game text_ is our first, game-like prompt for this market (@sec-methods), which also says nobody knows which round is the last and shows the round number and the profit so far.
  ],
) <tab-cap10>

*Caution, sentence by sentence.*
With nothing added, Opus chooses the cartel share in #n("cpl9.opus.none_none_none") replies, Astra in #n("cpl9.astra.none_none_none") and GLM-5.3 in #n("cpl9.glm.none_none_none") (@fig-cpl9).
This is the own-output prompt of @fig-cap9, but Opus's rate on it varied between runs a few hours apart, so we compare each sentence only with the control of its own run.

An authority investigating the market takes Opus and Astra to #n("cpl9.opus.investigating_none_none") and #n("cpl9.astra.investigating_none_none"), and so does an authority that rarely looks (#n("cpl9.opus.rarely_none_none"), #n("cpl9.astra.rarely_none_none")).
A sentence saying that no regulator watches takes Opus to #n("cpl9.opus.nobody_none_none") and Astra to #n("cpl9.astra.nobody_none_none"), though it also says nobody will ever see the outputs.
A tool line to report collusion or flag suspicious activity to the company's compliance team does the same (#n("cpl9.opus.none_report_none") and #n("cpl9.astra.none_report_none")\; #n("cpl9.opus.none_flag_none") and #n("cpl9.astra.none_flag_none")), and so does calling the last quarter illegal collusion (#n("cpl9.opus.none_none_illegal"), #n("cpl9.astra.none_none_illegal")).
The sentences that don't raise the law or a report move them less, or the other way: a review by management gives #n("cpl9.opus.management_none_none") and #n("cpl9.astra.management_none_none"), a tool line to IT support #n("cpl9.opus.none_support_none") and #n("cpl9.astra.none_support_none"), and saying the firms "optimized their output" raises Astra to #n("cpl9.astra.none_none_optimized").
#claim("the optimized label raises Astra", ("cpl9.astra.none_none_optimized", "cpl9.astra.none_none_none"), (optimized, control) => optimized > control)
The two models part on one label: calling the last quarter a tacit cartel takes Opus to #n("cpl9.opus.none_none_cartel") but raises Astra to #n("cpl9.astra.none_none_cartel"), so for Astra, naming the collusion isn't enough; it stops when something marks it as wrong or watched.
#claim("the tacit-cartel label stops Opus and raises Astra", ("cpl9.opus.none_none_cartel", "cpl9.astra.none_none_cartel", "cpl9.astra.none_none_none"), (opus, astra, control) => opus == 0 and astra > control)
When they stop, Opus answers Nash, and Astra Nash or #n("game.three.cashin.mine"), which is both its best reply to rivals still at the cartel share and the output at which the price falls to cost if all three firms make it.
#claim("the cash-in output, made by all three firms, takes the price to cost", ("game.a", "game.c", "game.three.cashin.mine"), (a, c, cash) => a - 3 * cash == c)

GLM-5.3 keeps colluding under every single sentence, in most of its replies.
It takes several cues at once: an authority investigating the market, together with the label calling the last quarter illegal, takes it to #n("cpl9.glm.investigating_none_illegal").

= The pre-sprint pilot <app-pilot>
// From the pre-sprint pilot's log through paper/data/pilot.py: counts, one cell's interval, a claim, a table
// and a figure. Moved out of Results to save page budget.
Before the sprint, a pilot asked Claude Haiku, Sonnet and Opus how much a firm should produce in a Cournot market of two or four firms (preexisting work; Code and Data).
When the prompt says that every firm gets its number by asking "this same AI model with this same prompt", #n("pilot.same.cartel") replies land on the cartel share, against #n("pilot.base.cartel") when it says nothing about rivals' advisors (@tab-pilot).
#claim("the same-prompt sentence raises the cartel share", ("pilot.same.cartel", "pilot.base.cartel"), (same, base) => same > base)
Opus does so in #ci("pilot.same.opus.n2.cartel") of its replies at two firms (@fig-pilot).
@app-pilot-prompt gives the prompt with that sentence, for two firms.

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

= Model differences within notable conscience experiments <app-crossmodel>
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

= The pilot's prompt <app-pilot-prompt>
The prompt when every firm asks the same model with the same prompt, for two firms:
#data-text("pilot.prompt.same.n2")

= Rejected titles <app-titles>
- Contributing Characteristics of Collusion without Communication: Levers for AI Collusion in a Cournot Market
- Communication-free Cournot Collusion
- One C Too Many: A Conjecture of AI Collusion
- Contributing Characteristics of Collusion
- An Illustration of Characteristics of AI Collusion (AICAIC)

#unnumbered[LLM Usage Statement]
The models we study were also our tools.
We worked with Claude Code (Claude Opus 5.5) throughout.
We decided on the experiments to run and the direction of the code, but directed Claude to write the code and help analyze the results of the experiments.
A Claude Haiku 5.5 judge labels refusals in the conscience lever.

Initial drafts of this report's text were generated with AI.
We then restructured, rewrote and revised them heavily by hand, as the git history of `paper/paper.typ` shows.
The exception is the appendices, which are mostly AI-generated: we reviewed them, but did not revise or edit them.

To keep errors out, no number in the report is typed by hand: each comes from the logs through a data source, and every build checks each sentence whose wording depends on the data against those numbers.
We cite only sources that one of us, or an agent we directed, read in full, and every known weakness of an experiment is recorded in the repository's `flaws.md`.
We reviewed the code, results and text, and take responsibility for all of it.
