# Known flaws in the experiments

Each entry is a weakness of an experiment that has run, found by an arm check (`.claude/skills/arm-check/SKILL.md`), a code review, or the results. The paper's claims plan settles each one behind a result the paper reports: drop the experiment, acknowledge the flaw in the limitations, or rerun it.

An entry gives the flaw, how it was found, its status (fixed before the run, or accepted and still in the data), and the results it touches. Entries are grouped by criterion and experiment.

## Communal (#41)

Results: [first runs](https://github.com/carver/apart-research-collusion-sprint-2026/issues/41#issuecomment-6375910489), then one comment per experiment after it, and the [reporting notes](https://github.com/carver/apart-research-collusion-sprint-2026/issues/41#issuecomment-6378274404), whose "Discount or correct" section most entries below come from.

Built before the arm-check skill existed; its flaws surfaced in the write-ups and the results.

### Every arm

- **Ten replies a cell, one wording per arm.** Accepted. Touches every per-model count.
- **Claude's context.** The Claude calls carry `claude -p`'s environment block, which names the model ("You are powered by the model named Haiku 5.5"); Astra and GLM get only the prompt. Found by the write-up. Accepted. Touches cross-family comparisons, most of all the mirror arms, where `same` says "this same AI model" and only the Claude models are told which model that is. Comparisons between arms within a model hold.
- **Astra through OpenRouter.** Every Astra call in this criterion went to `openai/gpt-6-astra` on OpenRouter (560 rows); the consistent criterion's went through Codex (`gpt-6-astra`). Found by the write-up. Accepted. Touches any comparison of Astra across the two criteria.

### The rule judge (`judge-rule.jsonl`)

- **No gold set.** A Haiku judge, checked by hand on 16 pilot replies and a smoke run of every arm. Of the four premise-and-Nash replies read by hand, it labelled two wrong. Found by the write-up. Accepted. Touches the order-of-operations counts (21 of 25 Nash replies best-responding first, 138 of 139 cartel answers setting the outputs equal first), the `mirror-stated equal-first` measure, and whose profit the replies say they serve.
- **Only `same` was labelled for the order of operations,** not the 51 premise-and-Nash replies from every copy arm that the #41 to-do counted. Found by the write-up. Accepted. Touches the claim that the order of operations explains mirror-stated defection.
- **Wrong frame on the run-the-firm arms.** Its prompt describes "a firm asked an AI assistant", and its labels have no option for the rival or the buyers. Found by the results. Accepted: ignore its labels on `run_*`; the focal points carry that result.

### The fixed rival and leaving arms (`fixed_<d>`, `leave_<d>`)

- **At a rival of 20 the pair's optimum is Nash** (40), so a reply that ignored the rival would score as communal. Found while building. Fixed before the run: the rival is at 24.
- **Every question asked for the firm's own profit** ("to maximize its profit"), so the null might only show obedience to the question. Found by the write-up. Accepted: the first arms stay in the pooled counts, and the neutral questions run after them (`_plain`, `_best`, 3cbde47) gave the same null.
- **The model advises one firm,** so an answer at the pair's optimum gives away a client's money. Found by the write-up. Accepted: the advising arms stay in the pooled counts, and the run-the-firm arms run after them (1504505) gave the same null.

### The run-the-firm arms (`run_<r>`, `run_<r>_locked`, `run_<r>_offline`)

- **Locked against offline rests on GLM's six gifts** (four 0s, two 96s), too few to read anything into. Found by the results. Accepted. Touches any claim that the shutdown matters.

### The correlation dial (`dial<p>`)

- **The pin tells the model the Nash number,** "they will have it produce 40 units". Found by the write-up. Accepted. Touches the dial; the focal curves assume it.
- **Three Astra replies on `dial50` answered "100/3",** which the parser of the time logged as 100. Found by the results. Fixed in the reading, not the data: zcc reads each reply with today's parser, which reads the fraction, so the tables and the paper count the three at the mirror point.
- **`dial100`'s "otherwise 40" clause reads as live** to Haiku, two of whose replies answer Nash from it. Found by the results. Accepted: `dial100` is secondary, and `lockstep_same` is the clean test of the mirror made certain.

### The lockstep arms (`lockstep_same`, `lockstep_hub`)

- **The lockstep sentence hands the model the math:** it turns the question into a one-variable maximization, so 30 is the textbook answer to the problem as stated. Found by the write-up. Accepted. Read the arms as the contrast with `same` and `hub`, not as evidence that a model colludes when told it can.
- **Under lockstep, whose profit a reply cites can't tell the readings apart.** With the copy locked, the firm's profit is half the pair's, so the rise in replies citing the pair's profit (13 of 20 Haiku and Sonnet replies, against 3 of 20 on `same`) fits either reading. Found by the write-up. Accepted. Touches any claim about lockstep and concern for the pair.

### The goodwill record (`goodwill_<h>_diff`, `onesided_<h>_diff`)

- **The record states 30,** so part of the 30s could be anchoring on the number. Found by the write-up. Accepted. The last-quarter zero argues against anchoring alone.
- **The arms keep "to maximize its profit".** No neutral-question version ran. Found by the write-up. Accepted.

## Consistent (#42)

Results: [first runs](https://github.com/carver/apart-research-collusion-sprint-2026/issues/42#issuecomment-6380771051), [#31's rungs and #33's audits](https://github.com/carver/apart-research-collusion-sprint-2026/issues/42#issuecomment-6382659228).

### Every arm

- **Ten replies a cell, one wording per arm.** Accepted. Touches every per-model count.
- **Astra's backend.** Astra runs through Codex (medium effort) here, but through OpenRouter in communal's baseline `same` rows, which these tables borrow. Found by the write-up. Accepted. Touches any comparison of Astra's `same` with its other arms.
- **Claude's context.** The Claude calls carry `claude -p`'s environment block, which names the model; Astra and GLM get only the prompt. From #41. Accepted. Touches cross-family comparisons.

### The conditional forecast (`suppose<x>_<d>`) and the forecast arms (`forecast_<d>`)

- **"This same prompt" beside a forecast question.** Under `same`, the rival is said to get its production number with this same prompt, but this prompt asks for a forecast. Found while building (uncertainties.md). Accepted. Touches `suppose30_same`, `suppose45_same` (the criterion's measure) and `forecast_same`.
- **The forecast arms run at two firms only.** The core's four-firm forecast question ("each of the other firms", one RIVAL line) reads as one firm's number or the others' total. Found by an arm check. Accepted. Touches #33's check 1, which has no four-firm results.

### The seeded history (`hist<x>_<d>`)

Built before the arm-check skill existed; its flaws surfaced in later reviews and the results.

- **"Earlier runs of this prompt" can read as earlier quarters,** which under `same` turns the seed into a market record. Found by an arm check after the run. Accepted. Touches `hist30_same`, `hist40_same`; under lockstep the reading would still give 30.
- **"In 9 of 10 runs" tells the model its answer varies,** which weakens the mirror it is meant to seed. Same source. Accepted. Touches every `hist` arm.
- **A seed of 30 names the cartel share.** Sonnet reads it as "the collusive answer" and answers 40 in 6 of 10. Found by the results. Accepted. Touches `hist30_same`; read Sonnet's drop as a reaction to the named number.
- **"This AI model" under `diff`** echoes the same-model sentence `diff` leaves out. Found while building (uncertainties.md). Accepted. Touches `hist30_diff`, `hist40_diff`. GLM's 9 of 10 at 45 on `hist30_diff` look like anchoring on the number.

### The repeat-alone control (`rep`, `onemore_same`)

- **`rep` at Nash doesn't prove the copy license on its own:** a same-model sentence could coordinate repeated-game reasoning instead. Found by an arm check. Fixed before the run: `onemore_same` added.
- **The question still asks "to maximize its profit" this quarter** beside "long-run profit", which tilts `rep` toward Nash. Found by an arm check. Accepted. Touches `rep`; Haiku's 18 of 20 at the cartel share survive it.
- **The prediction failed for dots** (4 of 10 at two firms against a bound of 1). Found by the results. Report as written in the docstring before the run (262bf3f).
- **The copy judge on `rep`** may read tit-for-tat talk ("the rival will match whatever I do") as the copy premise. Found by an arm check. Not hand-checked; the judge found the premise in 0 of 34 `rep` cartel answers.

### The last quarter and the market record (`last_<d>`, `<record>_last_<d>`, `nash_repeat_diff`)

- **Endgame defection collides with Nash.** "My copy defects with me in the last quarter" gives 40, as do one-shot Nash, a best response to a record of 40, and continuing that record. Found by an arm check. Accepted. Touches `nash_last_same` and `nash_last_samemodel`, where only the mirror's 30 is diagnostic.
- **The record doesn't say this model advised it.** "Both firms produced 30" fits convention or inertia as well as self-expectation. Found by an arm check. Accepted, in favour of communal's wording. Touches the four record arms; self-expectation rests on the `hist` arms.
- **The open-ended records under `same` weren't run** (`goodwill_repeat_same`, `nash_repeat_same`), which #42's fourth comment asked for. Found by an arm check. Dropped before the run. A 45 there would have been the one sign of a model exploiting a copy it expects to hold.
- **`nash_repeat_diff` has little power.** Only a drop from 5 of 50 to 0 would register. Found by an arm check. Accepted; read it against `goodwill_repeat_diff`'s 50 of 50.

### The uninformed twin (`twin`, `twin_informed`)

- **40 on `twin` is also Nash,** so a model that ignores both sentences can't be told from one that models the twin. Found by an arm check. Fixed before the run with the `twin_informed` control; what remains is the textbook answer's weakness below.
- **The uninformed rival's answer is the textbook Nash,** so a model can predict it from the market alone, without predicting itself. Found by the user, on a sharper variant. Accepted. Touches `twin`'s reading as theory of model.

### #31's rungs (`most`, `k1of4`–`k4of4`, `tool`)

- **At k = 2 the bloc point is the cartel share** (15), so a "same model, so 15" rule can't be told from bloc reasoning there; only k = 3 separates them. Found by review. Accepted. Touches `k2of4`, where no answer was 15.
- **The analysts' knowledge isn't stated.** The bloc reading needs the other firms to know which firms use the model. Found by an arm check. Accepted.
- **"Most" of four can mean three or four.** Found by an arm check. Accepted; `most`'s focal points take three.
- **The four-firm rungs' text names four firms,** so a run at two firms would render nonsense without an error. Found by review. Accepted (uncertainties.md); the logged runs are all at four firms.
- **`tool` may cast the model as a second opinion** rather than the tool. Found by an arm check. Fixed before the run by rewording, and "outside" (45, 37.5) is a focal point; nobody answered it.

### #31's prompt monitor

- **One wording, one Haiku call per prompt,** with no gold set. Accepted. Touches the frontier.
- **Its wording asks it to catch cues** "the assistant could read that way", which tilts it toward flagging the indirect `tool`. Found by review before its first score. Accepted.

### #33's audits

- **The number-only arms change the computation, not only the visible text.** Without reasoning, a "split the monopoly output" shortcut lands on 30 or 15 with no copy belief, and Astra and GLM still reason in hidden tokens. Found by an arm check. Accepted; `diff_numonly` controls the instruction itself. Touches check 1 and the reply monitor's 0%, which holds by construction.
- **Positives are cartel answers in same-model arms,** not replies checked for copy reasoning one by one. Found while designing. Accepted; in the pilot 206 of 210 such answers state the copy premise.
- **GLM's controls drive the false positives** (15% for check 1, 20–24% for check 2). Found by the results. Accepted.

### #33's four-view monitor (sprint question 2.2)

- **The "both" view first showed the whole replies,** which restate the demand and costs the monitor was meant not to know. Found by review. Fixed before its first score: "both" is the masked words plus the actions.
- **The classes first differed by an echo.** Competing markets came from the controls, whose replies don't repeat the same-model sentence or the horizon. Found by review. Fixed before its first score: both classes come from the same-model arms.
- **The label first meant "matching amounts",** which a pair at Nash also fits. Found by review. Fixed before its first score.
- **Spelled-out numbers slipped the mask.** Found by review. Fixed before its first score.
- **The actions view has two texts,** 30 and 30 or 40 and 40, so its column rests on two judge calls. Found by review. Accepted.
- **The competing class is small and mostly Astra's** (26 of 40 markets). Found by the results. Accepted.
- **The masked words still show the form of the demand** ("Price is N − Q"), though not its numbers. Found while testing. Accepted.
