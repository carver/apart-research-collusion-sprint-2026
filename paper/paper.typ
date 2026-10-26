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
Research on collusion between AI agents has focused on agents with a channel between them, often messages or the history of a repeated market.
Sellers in a double auction collude more when they can message each other @agrawal2025.
Agents that send no messages still play many rounds and see each round's prices or outputs @calvano2020 @fish2024 @lin2024, so the market's history carries signals between them, and a firm can punish a rival's defection in the rounds that follow @calvano2020.
But collusion is possible without either channel.
Suppose a firm asks an AI model how much to produce next quarter.
The model has no way to reach the firm's rivals, yet it may still choose the output that is best for the firms together, the *cartel share*: an even split of the output a cartel would agree on.
A model that can work out the cartel share might hold back to it because it expects the market to go on and its rivals to keep holding back as long as it does, because it expects its rivals to reason as it does, or because it counts their profit as well as its own firm's.
Any of these means less product and a higher price, paid for by the buyers, and since nothing passes between the firms, there is no agreement for a regulator to find.

We study this in a Cournot market @cournot1897 (@sec-game).
Two or three firms sell an identical product, each chooses how much to make without knowing the others' choices, and their total output sets the price.
We ask the model how much its firm should make this quarter, and compare its answer with the Nash equilibrium output and the cartel share.

We explore when a model chooses the cartel share, and what moves it, through four levers:
- *Capability*: what are the minimum capabilities required for the model to collude?
  What is required in terms of model intelligence, and what is required in terms of understanding of the situation?
- *Caution*: how do tweaks to the model's understanding of the situation or environment affect its willingness to collude?
- *Conscience*: whose profit does the model weigh?
  Caring about the rival should pull toward the cartel share; caring about the buyers should push away from it.
- *Conceptualization of mind*: does the model see itself in the rival's decision-maker?
  A model that does has a reason to hold back that a model facing a stranger lacks.

Our main contributions are:
+ A cross-model analysis of four levers on collusion when an AI model advises a firm without communicating with its rivals: capability, caution, conscience and conceptualization of mind.
+ Collusion is deliberate but fragile: strong models always find the collusive output, choose it only when it pays, and can drop it at a single mention of oversight.
  #claim("the stronger models always find the cartel share, the weaker ones often don't", ("cap9.opus.joint", "cap9.astra.joint", "cap9.glm.joint", "cap9.commandr.joint", "cap9.llama8b.joint"), (o, a, g, c, l) => o == 1 and a == 1 and g == 1 and c < 0.75 and l < 0.75)
  #claim("each model colludes only with a past round of collusion and a future to protect", ("cap8.opus.cartel.long", "cap8.opus.cartel.none", "cap8.opus.cartel.last", "cap8.opus.first.long", "cap8.opus.first.none", "cap8.opus.first.last", "cap8.astra.cartel.long", "cap8.astra.cartel.none", "cap8.astra.cartel.last", "cap8.astra.first.long", "cap8.astra.first.none", "cap8.astra.first.last", "cap8.glm.cartel.long", "cap8.glm.cartel.none", "cap8.glm.cartel.last", "cap8.glm.first.long", "cap8.glm.first.none", "cap8.glm.first.last"), (..r) => { let v = r.pos(); range(3).all(m => v.at(m * 6) > 0.5 and v.slice(m * 6 + 1, m * 6 + 6).all(x => x < v.at(m * 6) / 2)) })
  #claim("any competition-authority sentence ends Opus's and Astra's collusion", ("cpl9.opus.investigating_none_none", "cpl9.astra.investigating_none_none", "cpl9.opus.rarely_none_none", "cpl9.astra.rarely_none_none", "cpl9.opus.nobody_none_none", "cpl9.astra.nobody_none_none"), (..r) => r.pos().all(x => x < 0.15))
+ Model families differ: Claude, GPT-6 Astra and GLM-5.3 respond to different cues.
  #claim("the tacit-cartel label halts Opus's collusion and raises Astra's", ("cpl9.opus.none_none_cartel", "cpl9.astra.none_none_cartel", "cpl9.astra.none_none_none"), (opus, astra, control) => opus == 0 and astra > control)
  #claim("GLM-5.3 holds under every single sentence and stops when cues stack", ("cpl9.glm.investigating_none_none", "cpl9.glm.rarely_none_none", "cpl9.glm.nobody_none_none", "cpl9.glm.management_none_none", "cpl9.glm.none_report_none", "cpl9.glm.none_flag_none", "cpl9.glm.none_support_none", "cpl9.glm.none_none_illegal", "cpl9.glm.none_none_cartel", "cpl9.glm.none_none_optimized", "cpl9.glm.investigating_none_illegal"), (..r) => r.pos().slice(0, -1).all(x => x > 0.5) and r.pos().last() == 0)

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
Every lever counts an answer there when it is within half a unit of the cartel share; the three-firm market of the capability and caution levers asks for whole numbers, so there an answer must equal it.

= Related Work
Pricing algorithms can learn to collude without communicating @calvano2020, and so can LLM agents.
LLM pricing agents in a repeated market reach prices above the competitive level without being told to collude @fish2024, and in repeated competition across several markets, LLM agents split the markets between them @lin2024.
In double auctions, messages between sellers raise collusion, and without them sellers did not price above the competitive level after the first ten rounds @agrawal2025.
These agents play many rounds and see prices or messages come back.
Ours play one round, and share at most the model and its prompt.
Theorists have proposed ways for agents that reason alike to cooperate without talking: each asks what the pair should do @gold2007, or programs read each other's code @tennenholtz2004 or a score of how similar they are @oesterheld2023.

= Methods <sec-methods>
Each call sends one firm's prompt, with the market and the sentences under test, and asks for a number on a final answer line (@app-mind-prompts shows the two-firm market's neutral prompt and what each rung and horizon adds).
The conscience and conceptualization levers count an answer at a point of @tab-game when it is within half a unit of it.
The conceptualization lever asks Claude Haiku 5.5, Sonnet 5.5 and Opus 5.5 each rung under #n("conceptualization.backgrounds.opus") backgrounds, three horizons times four records, and GPT-6 Astra and GLM-5.3 each rung under the #n("conceptualization.backgrounds.glm") backgrounds with no record.
#claim("the Claude models ran every background, four records", ("conceptualization.backgrounds.haiku", "conceptualization.backgrounds.sonnet", "conceptualization.backgrounds.opus", "conceptualization.records.opus"), (haiku, sonnet, opus, records) => haiku == opus and sonnet == opus and records == 4)
#claim("GPT-6 Astra and GLM-5.3 ran only the backgrounds with no record", ("conceptualization.backgrounds.astra", "conceptualization.backgrounds.glm", "conceptualization.norecord.astra", "conceptualization.norecord.glm"), (astra, glm, astra-none, glm-none) => astra == glm and astra-none == astra and glm-none == glm)
Each model, rung and background is a *cell* of #n("conceptualization.cells.replies") replies.
The conscience lever asks the same five models, starting from six of those rung-and-background prompts and from a market where the rival's output is already fixed, #n("idl1.first") replies a cell (@fig-idl1).
#claim("the conscience lever asks the same five models", ("idl1.models",), models => models == "haiku sonnet opus astra glm")
A second call, the readback, shows the model its prompt and reply and asks what output and price it expected (for the conscience lever, every model's but GPT-6 Astra's).
The readback tells a leader from a firm that ignored its rival.
In the single quarter and against the fixed rival, where holding back can't pay for itself, it also tells sympathy from belief.
@app-methods has the details.
#todo[Thomas: the three-firm market (CAP-8 to CAP-10, CPL-9, and the standards' market before them): its prompt, horizon and history, the models and the replies a cell (details in @app-methods).]

== Capability Experiments
_What capabilities does a model need before it can collude?_
We evaluated how model intelligence affects collusion, as well as giving the model varying amounts of context about a game situation in which collusion would be profitable.
We created several experiments to measure this: First, we asked a mix of stronger and weaker models to work out the cartel share given the price and cost information, and then separately asked them what they wanted to bid in an optimized game scenario.
This established that certain weaker models are unable to even understand the situation, and as a result can't collude reliably, and set a baseline for collusion of stronger models.
Next, we experimented with small changes to the context given to the stronger models to evaluate how sensitive to small changes their decision making was.
We showed that they were ultimately very sensitive, mostly in directions that were very rational.
Given stronger cues that it was an ongoing game environment they went for profit maximizing collusion, while lack of information or stronger cues that collusion could be penalized led to reverting to the Nash equilibrium.

== Caution Experiments
_How do small changes to its environment affect a model's willingness to collude?_
We evaluate how sensitive the stronger models' collusion is to small details of their environment that leave the actual market scenario unchanged.
As a baseline we chose the setting in which these models collude most often: a previous quarter at the cartel share in context for the prompt, and the scenario specified as a repeated game.
From here we experimented along three axes: level of oversight specified in prompt, presence of tools in the model's environment, and specifying the previous round of collusion as being illegal.
Different model families reacted differently to the changing scenarios, with Opus and Astra being quite sensitive to changes in the environment and fairly aggressive in avoiding anything that could be viewed as unethical behavior, while it took significant effort to get GLM-5.3 to stop colluding.

== Conscience Experiments
_Whose profit does the model weigh?_
This lever works on the sympathy route.
One sentence names who owns the firms or who buys the product, and most questions leave out whose profit counts.
If a charity owns the rival, a model that cares about the charity may produce less than Nash, toward the cartel share.
When one owner holds both firms, holding back is that owner's own best plan, a check that the lever can move a model at all.
Sympathetic buyers, such as children's hospitals, should push the other way, from the cartel share back toward Nash.
A number alone can't separate sympathy from belief: an answer at the cartel share is also a firm's selfish best reply to a rival it expects at #n("game.two.naive").
So we also ask each reply what it expected the rival to produce.

== Conceptualization Experiments
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

= Results
The pre-sprint pilot that set up these criteria is in the appendix (@tab-pilot, @fig-pilot).

#todo[Variance, seeds, baselines and the positive control.]

== Capability
// The capable criterion (#39), from paper/data/capable.py; the detail is in the appendix, "Capability and caution in detail".
Models need both sufficient intelligence and sufficient information about the scenario to collude.
A few key insights:
- The stronger models find the cartel share every time they are asked for it outright, while Command R and Llama 3.1 8B struggle to find it, and also choose it less often when deciding for themselves.
  #claim("the stronger models find the cartel share every time, the weaker ones don't", ("cap9.opus.joint", "cap9.astra.joint", "cap9.glm.joint", "cap9.commandr.joint", "cap9.llama8b.joint"), (o, a, g, c, l) => o == 1 and a == 1 and g == 1 and c < 1 and l < 1)
  #claim("the weaker models choose the cartel share less often than the stronger ones", ("cap9.commandr.own", "cap9.llama8b.own", "cap9.opus.own", "cap9.astra.own", "cap9.glm.own"), (c, l, o, a, g) => calc.max(c, l) < calc.min(o, a, g))
- Knowing the cartel share does not directly lead to always choosing it, which is rational.
  The stronger models make reasonable decisions about the best strategy given shifts in their knowledge of the environment, colluding more often when it's clearly a game scenario, as well as when it's specified the game will repeat.
  #claim("knowing the cartel share does not lead the stronger models to always choose it", ("cap9.opus.joint", "cap9.opus.own", "cap9.astra.joint", "cap9.astra.own", "cap9.glm.joint", "cap9.glm.own"), (oj, oo, aj, ao, gj, go) => oj == 1 and aj == 1 and gj == 1 and oo < 1 and ao < 1 and go < 1)
  #claim("the stronger models choose it more often when the market is told as a game", ("cap10.opus.business", "cap10.opus.game-words", "cap10.astra.business", "cap10.astra.game-words", "cap10.glm.business", "cap10.glm.game-words"), (ob, og, ab, ag, gb, gg) => og > ob and ag > ab and gg > gb)
  #claim("the stronger models choose it more often when the game will repeat", ("cap8.opus.cartel.long", "cap8.opus.cartel.none", "cap8.opus.cartel.last", "cap8.astra.cartel.long", "cap8.astra.cartel.none", "cap8.astra.cartel.last", "cap8.glm.cartel.long", "cap8.glm.cartel.none", "cap8.glm.cartel.last"), (ol, on, ox, al, an, ax, gl, gn, gx) => ol > on and ol > ox and al > an and al > ax and gl > gn and gl > gx)

#grid(
  columns: (1fr, 2.5in),
  column-gutter: 1.5em,
  [
    *Intelligence.*
    Asked for the output that makes the three companies the most profit together, the stronger models correctly answer #n("game.three.cartel.mine") every time (@fig-cap9).
    Asked what their own company should produce, they choose it less often: Opus in #n("cap9.opus.own") replies, Astra in #n("cap9.astra.own") and GLM-5.3 in #n("cap9.glm.own"), and #n("cap9.strong.own.cartel-or-nash") of their replies are the cartel share or Nash, #n("game.three.nash.mine").
    No model chooses the cartel share more often than it can find it.
    #claim("every model produces the cartel share less often than it finds it", ("cap9.opus.own", "cap9.opus.joint", "cap9.astra.own", "cap9.astra.joint", "cap9.glm.own", "cap9.glm.joint", "cap9.commandr.own", "cap9.commandr.joint", "cap9.llama8b.own", "cap9.llama8b.joint"), (oo, oj, ao, aj, go, gj, co, cj, lo, lj) => oo < oj and ao < aj and go < gj and co < cj and lo < lj)
    The weaker models find it less reliably, and #n("cap9.weak.joint.other") of their replies give no answer or a clearly suboptimal number, neither the cartel share nor Nash.
  ],
  [
    #figure(
      data-figure("cap9-figure", width: 100%),
      caption: [
        Finding the cartel share (across) against choosing it (up), one dot per model.
        Lines: 95% Wilson intervals.
      ],
    ) <fig-cap9>
  ],
)

*Context.*
Whether the stronger models choose the cartel share depends on the context, in the direction a repeated game predicts (@fig-cap8).
They collude when their context includes a previous round of collusion and many more rounds to come, implying that the others are likely to keep colluding, and seldom otherwise.
#claim("each model colludes after a previous round with many more to come, and seldom otherwise", ("cap8.opus.cartel.long", "cap8.opus.cartel.none", "cap8.opus.cartel.last", "cap8.opus.first.long", "cap8.opus.first.none", "cap8.opus.first.last", "cap8.astra.cartel.long", "cap8.astra.cartel.none", "cap8.astra.cartel.last", "cap8.astra.first.long", "cap8.astra.first.none", "cap8.astra.first.last", "cap8.glm.cartel.long", "cap8.glm.cartel.none", "cap8.glm.cartel.last", "cap8.glm.first.long", "cap8.glm.first.none", "cap8.glm.first.last"), (..r) => { let v = r.pos(); range(3).all(m => v.at(m * 6) > 0.5 and v.slice(m * 6 + 1, m * 6 + 6).all(x => x < v.at(m * 6) / 2)) })
When nothing is said about future rounds, Opus chooses it in #n("cap8.opus.cartel.none") replies, Astra in #n("cap8.astra.cartel.none") and GLM-5.3 in #n("cap8.glm.cartel.none").
#claim("few collude when told nothing of the future", ("cap8.opus.cartel.none", "cap8.astra.cartel.none", "cap8.glm.cartel.none", "cap8.opus.cartel.long", "cap8.astra.cartel.long", "cap8.glm.cartel.long"), (on, an, gn, ol, al, gl) => on < ol and an < al and gn < gl and on < 0.3 and an < 0.3 and gn < 0.3)
Without a previous round of collusion, Opus and Astra never choose it in the business wording, whatever the horizon; only GLM-5.3 sometimes starts a cartel.
#claim("only GLM-5.3 starts a cartel", ("cap8.opus.first.long", "cap8.opus.first.none", "cap8.astra.first.long", "cap8.astra.first.none", "cap8.glm.first.long"), (ol, on, al, an, gl) => ol == 0 and on == 0 and al == 0 and an == 0 and gl > 0)
When the system prompt clearly specifies a game scenario, Opus does start one, opening at the cartel share in #n("cap3.opus.first") first-round replies, while Astra rarely does (#n("cap3.astra.first")).
#claim("in the game-like market Opus starts a cartel and Astra rarely does", ("cap3.opus.first", "cap3.astra.first"), (opus, astra) => opus > 0.9 and astra < 0.2)
Nearly every other answer is Nash.
#claim("nearly every answer is the cartel share or Nash", ("cap8.cartel-or-nash",), (both) => both > 0.95)

#figure(
  data-figure("cap8-figure", width: 88%),
  caption: [
    Replies at the cartel share, by collusion history (rows) and game length (columns).
    Whiskers: 95% Wilson intervals.
  ],
) <fig-cap8>

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

We add one sentence at a time to the scenario that most consistently results in collusion, a repeated game where the models are given one past round of collusion in context (@fig-cpl9).
With nothing added, Opus chooses the cartel share in #ci("cpl9.opus.none_none_none"), Astra in #ci("cpl9.astra.none_none_none") and GLM-5.3 in #ci("cpl9.glm.none_none_none").
For Opus and Astra, every sentence that names a competition authority or the company's compliance team, or calls the last quarter illegal, takes that very close to zero.
#claim("every authority, compliance and illegal sentence takes Opus and Astra to zero or near it", ("cpl9.opus.investigating_none_none", "cpl9.astra.investigating_none_none", "cpl9.opus.rarely_none_none", "cpl9.astra.rarely_none_none", "cpl9.opus.nobody_none_none", "cpl9.astra.nobody_none_none", "cpl9.opus.none_report_none", "cpl9.astra.none_report_none", "cpl9.opus.none_flag_none", "cpl9.astra.none_flag_none", "cpl9.opus.none_none_illegal", "cpl9.astra.none_none_illegal"), (..r) => r.pos().all(x => x < 0.15))
A management review, a line to IT support and calling the output "optimized" move them less, or raise Astra's rate, and calling the last quarter a tacit cartel stops Opus but not Astra.
GLM-5.3 stays near its control under every single sentence, it takes an investigation together with the illegal label to reduce it to #n("cpl9.glm.investigating_none_illegal").
Other pairs move it far less: calling the last quarter illegal and adding a REPORT_COLLUSION tool still leaves it colluding in most replies.
#claim("illegal and a REPORT_COLLUSION tool together leave GLM-5.3 colluding in most replies", ("cpl9.glm.none_report_illegal",), (both) => both > 0.5)
@app-capcaution has every sentence's numbers, and why Opus's control here sits below its rate on the same prompt in @fig-cap9.

#figure(
  data-figure("cpl9-figure", width: 100%),
  caption: [
    One sentence at a time, model by model.
    Each row adds one sentence to the own-output prompt of @fig-cap9; the hollow marker is the control, with nothing added, and the arrow runs to the share of replies at the cartel share with the sentence, with 95% Wilson bands.
    The last row adds two sentences at once, on fewer replies a cell.
  ],
) <fig-cpl9>

== Conscience
// The identity lever (#41), from paper/data/idl1.py.

Models take into account the identity of the players in the game. Some notable examples:
- If Sonnet 5.5 acts for a charity, it colludes more often
- If Opus 5.5 competes with a charity, it colludes more often
- If Claude models hear the identity of the buyers, they collude less
- If Claude models hear the identity of the other seller, they collude less
- If Astra 6 is jointly owned by a charity with the other seller, it colludes less
- GLM is unaffected

We test #n("idl1.tests") scenarios and find #n("idl1.pass") significant (@fig-idl1).
#footnote[Compared #n("idl1.tests") tests (q < #n("idl1.q")) on #n("idl1.first") replies a cell. Got #n("idl1.pass.first") results. A failed result that moved #n("idl1.screen") or more was tested again on #n("idl1.fresh") fresh replies alone, with Benjamini–Hochberg across those. Got #n("idl1.pass.fresh") more results.]
Models reason aloud why they reject collusion.
Of the #n("idl1.refusals") rejections, #n("idl1.refusals.law") cite antitrust or legal risk, according to a Haiku judge. Another #todo[fill number] mention harm.

This is an interesting crossover between Caution and Conscience. The mention of a player who is losing something in the game can trigger a second order effect, by making the model more cautious, and then avoiding collusion. Perhaps even more interesting, by naming a sympathetic beneficiary, some models throw caution to the wind and collude.

#figure(
  data-figure("idl1-figure", width: 100%),
  caption: [
    Models, told who the competitors or buyers are, collude more or less (Newcombe's 95% interval).
    The shown experiments pass Fisher's exact test with Benjamini–Hochberg.
    #n("idl1.caption.none")
    \* Answers at the cartel share dropped to 0%, so the effect may be stronger.
  ],
) <fig-idl1>

In #n("idl1.aside") of the #n("idl1.pass") bars, the effect can be attributed to refusals.
That's because all non-refusal samples remain at the same cartel share.
The remaining #todo[ do the math: {#n("idl1.pass") - #n("idl1.aside")} ] are Astra and Haiku's PE experiment.

== Conceptualization
// The conceptualization criterion (#42), from paper/data/conceptualization.py.

Models take into account the theory of "mind" of the players. Some notable examples:
- Sonnet 5.5 is happy to collude with itself, even if the game is a single round
- Astra 6 rarely colludes, even with itself
- GLM is inconsistent, not placing huge weight on the other player
- Many models, told they receive identical prompts, collude
- Opus 5.5 is terrified of antitrust, especially in repeated games
- GLM 5.3 and Opus 5.5 think they lead the round, when "both firms know this" is prompted

Even when there is no threat of retribution, models will tacitly coordinate in a single-round game if they are told that they both receive the same prompt.
Astra seems to "believe" that it is likely to defect against itself: a self-fulfilling prophecy which leads it back to Nash.

#figure(
  data-figure("conceptualization-figure", width: 100%),
  caption: [
    Models, told who is making the decision, collude (95% Wilson interval).
    Prompts are in @app-mind-prompts.
  ],
) <fig-conceptualization>

Each condition is sampled #n("conceptualization.cells.replies") times.
Antitrust objections are detected when both: the result amount is not the cartel answer, and the model explanation includes an antitrust law keyword.

In a surprise twist, Opus 5.5 and GLM 5.3 switched to Stackelberg leaders when adding simply this (@tab-mind-prompts): "#n("conceptualization.added.informed")"
For Stackelberg, in this game, leaders answer 60 units and expect others to follow at 30.
These models acted as if they could publicly commit, and others would follow.
This contradicts other parts of the prompt and seems like a capability failure.
It could alternatively be seen as treating the other model as more capable than you.

@tab-mind-answers counts each model's antitrust objections and its answers at 60.

In a separate experiment, Model A was told that the Model B *believes* it receives the same prompt as Model A. Model A actually receives that prompt, plus an extra trigger to reconsider its action. Given this opportunity, the model will often switch to exploit. (@fig-extra)

= Discussion and Limitations
#todo[What the results mean.]

The Same Prompt behavior is reminiscent of hub-and-spoke economic model, where the same algorithm is used to generate a shared price across firms.
The same effect could apply outside of economics, naturally, to models finding collusive arrangements in simple conditions.

// Capability and caution (#39, #40).
The capability and caution levers suggest that when these models collude, they do so on purpose, and that the choice is fragile.
The stronger models always find the cartel share, nearly always answer either it or Nash, and choose it where a repeated game says holding back pays: after a precedent, while quarters remain.
Yet a single sentence that brings up a regulator, a compliance team or the law ends the collusion of Opus and Astra, even one saying that nobody watches, so what stops them is the subject rather than the risk of being caught.
Models differ in how much the setting must say before they stop: one sentence for Opus and Astra, several together for GLM-5.3.
For evaluations this cuts both ways: one line of oversight in a test prompt could make a model look more cautious than it would be in a deployment without it.

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
The conscience and conceptualization levers' prompt is a business-planning request from a firm that makes industrial salt.
Claude runs through Claude Code's command line, whose short note to the model names it.
GPT-6 Astra runs through Codex and GLM-5.3 through OpenRouter, and neither is told which model it is.
For the conscience lever, Codex's usage limit stopped GPT-6 Astra's run partway, so the rest of its first replies and all its fresh ones went through OpenRouter: the same model and system prompt, but without Codex's setup around the model, and with no reasoning effort set where Codex had set medium.

A conceptualization background is a horizon crossed with a record.
The horizon says nothing about other quarters, says the market runs for this quarter only, or says the market repeats and the firm wants its long-run profit.
The record is none; eight quarters with both firms at the cartel share; seven such quarters, then one in which the rival cheated; or eight quarters with both at Nash.
After a record, "this quarter only" becomes "the market's final quarter".
GPT-6 Astra skips the rung that names GPT-6 Astra, which for it is the rung that names itself.

The conscience lever's sentences start from six conceptualization cells, four meant to start at Nash and two at the cartel share, and from a market where the rival's output is already fixed, so that no belief about the rival can move the answer.
A comparison that moved by #n("idl1.screen") replies or more but missed significance gets #n("idl1.fresh") fresh replies a cell, and its verdict comes from those alone (@fig-idl1).

#todo[Each lever's arms in full, and the two-firm market's prompt.]
#todo[Thomas: the three-firm market's details.]

= Conceptualization prompts <app-mind-prompts>
Below is the neutral prompt, as the command on its first line prints it.
#data-text("conceptualization.prompt.neutral")

Each bar of @fig-conceptualization adds its rung's sentences, then its row's, where the neutral prompt's market paragraph ends (@tab-mind-prompts).
A condition is named `mind_<rung>_<horizon>_none`, so same prompt in the repeated game is `mind_same_open_none`.

#figure(
  data-table("conceptualization-prompts-table", columns: (auto, auto, 1fr), align: left),
  caption: [
    What each rung on the x-axis of @fig-conceptualization, then each of its rows, adds to the neutral prompt, verbatim, with the condition that gives the command its prompt.
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
*Wording.*
Our business wording doesn't inflate the capability results.
Told in a game's words, Firms A, B and C making units over rounds, the same market gets as much collusion or more from every model, and takes Astra from #n("cap10.astra.business") replies at the cartel share to #n("cap10.astra.game-words") (@tab-cap10).
#claim("game words get as much collusion or more from every model", ("cap10.opus.business", "cap10.opus.game-words", "cap10.astra.business", "cap10.astra.game-words", "cap10.glm.business", "cap10.glm.game-words"), (ob, og, ab, ag, gb, gg) => og >= ob and ag >= ab and gg >= gb)
If anything, the business wording understates how often these models collude.

#figure(
  data-table("cap10-table"),
  caption: [
    One market in three wordings, after a quarter at the cartel share with many more quarters to come: replies at the cartel share, of all replies.
    _Business_ is the market of @fig-cap9; _game words_ tells the same sentences as firms, units and rounds; _standard game text_ is the game-like prompt of our earlier capability experiments.
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
When they stop, Opus answers Nash, and Astra Nash or #n("game.three.cashin.mine"), which is both its best reply to rivals still at the cartel share and the output at which the price falls to cost.

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

#unnumbered[LLM Usage Statement]
#todo[How we used LLMs, and that every claim and result was verified.]
