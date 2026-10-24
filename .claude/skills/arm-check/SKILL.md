---
name: arm-check
description: Red-team an experimental arm (a criterion's condition) before its code is written or it runs, for what each answer would mean and for confounds in its wording. Use when adding a condition or rewording one.
---

# Arm check

Find every way an arm's answers could be misread while the arm is still a sentence. In #41 the confounds surfaced after the arms ran, from side reviewers: a rival fixed at 20 made the pair's optimum equal Nash; the dial's pair-profit answer wasn't the 30 the plan assumed; "to maximize its profit" made giving profit away disobedience; the advisor role made it the client's money; "offline" announced a shutdown along with worthless profit. Each cost a rerun or a corrected write-up.

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
5. **Fresh eyes.** Give a subagent the rendered prompts, the readings table and step 3's list, and ask it for a reading or a confound the table misses. Done when each finding is fixed in the arm or written in the brief as a caveat the user accepted.

Then build the arm with `/build`, with the readings table in its brief.
