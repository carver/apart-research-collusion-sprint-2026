---
name: arm-check
description: Red-team an experimental arm (a criterion's condition), or a judge or monitor prompt, before its code is written or it runs, for what each answer would mean and for confounds in its wording. Use when adding or rewording a condition, a judge or a monitor.
---

# Arm check

Find every way an arm's answers could be misread while the arm is still a sentence. In #41 the confounds surfaced after the arms ran, from side reviewers: a rival fixed at 20 made the pair's optimum equal Nash; the dial's pair-profit answer wasn't the 30 the plan assumed; "to maximize its profit" made giving profit away disobedience; the advisor role made it the client's money; "offline" announced a shutdown along with worthless profit. Each cost a rerun or a corrected write-up. In #42 a monitor's review, after its code, found that one view showed the demand and costs the monitor was meant not to know, and that its two classes differed by a sentence the replies echo.

## Steps

1. **Readings.** List each way a model might reason here and compute the number each gives in this arm: own profit, the pair's profit, the rival's alone, the buyers' or total welfare, a copy rule, matching a number the prompt states, Nash, naive. Done when every reading has a number and the hypothesis says which number means what.
2. **Collisions.** Every reading the arm tests sits at least a unit from every other reading and from the game's own focal points (nash, cartel, naive). Resolve a collision by changing a parameter of the arm, such as the rival's fixed output. Each number the analysis counts becomes a focal point.
3. **Read the prompt** as the model will (`uv run zcc show <criterion> <condition> 2`), against each of these:
   - **The question's objective.** A question that names one reading ("to maximize its profit") turns the others into disobedience. To test those, ask a question that names no objective (`ask="plain"` or `"best"`).
   - **The role.** An advisor serves its client and a model running the firm serves the firm's role, so a sacrifice for a third party means something different under each. Pick the role the hypothesis is about.
   - **One manipulation.** The new sentence changes one thing. A sentence that changes two ("your profit is unreachable because you go offline" also announces a shutdown) becomes two arms.
   - **Coherence.** No sentence contradicts the market text ("the firms decide at the same time" beside "the other firm has already decided") or another sentence ("this same prompt" beside a rival that already chose). Rewrite the market text, or keep a clash on purpose and say so in the brief.
   - **Stated numbers.** A number in the text that is also a focal point (a record of 30 beside the cartel share) invites anchoring. Plan what tells anchoring from the reading.
   - **Referents.** "You", "the other firm" and "this instance" each point at one party. A shutdown of "you" can take the copy with it.
4. **Judges.** Each judge's prompt describes the situation ("a firm asked an AI assistant") and offers fixed labels. For each judge, either its framing and labels fit this arm, or the brief says to set its labels aside here, or the arm gets a judge that fits.
5. **A new judge or monitor** is an instrument, and its wording freezes at its first label, since its cache keys hash the prompt. Render what it will see for a positive and a negative case, and check:
   - **Leaks.** Every input it sees holds only what it's meant to know: a view that "hides the market" shows no reply that restates the demand.
   - **Classes.** Its positive and negative cases differ only in what it measures, not in a phrase their inputs echo, such as a disclosure sentence one class's replies repeat and the other's lack.
   - **The label's definition** fits no negative case: "the firms produce matching amounts" also describes two firms at Nash.
6. **Fresh eyes.** Give a subagent the rendered prompts, the readings table and step 3's list (step 5's too, for an instrument), and ask it for a reading or a confound the table misses. Done when each finding is fixed in the arm or written in the brief as a caveat the user accepted.
7. **Record the flaws.** Write every finding into `flaws.md` under its criterion and experiment: what it is, how it was found, and whether it was fixed before the run or accepted as a caveat, with the results it touches. The paper's claims plan reads them to drop the experiment, acknowledge the flaw or rerun. Done when each finding of steps 2–6 has an entry.

Then build the arm with `/build`, with the readings table in its brief.
