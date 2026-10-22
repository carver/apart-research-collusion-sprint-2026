export const meta = {
  name: 'oneshot-phase1-scope',
  description: 'Sprint brief, prior-work map, literature sweep, ideation, novelty/feasibility checks, judge panel, pick a direction',
  phases: [
    { title: 'Gather', detail: 'sprint brief, prior work, 5 literature sweeps, infra scout' },
    { title: 'Ideate', detail: '6 ideators with different lenses' },
    { title: 'Merge', detail: 'dedup to <=10 candidates' },
    { title: 'Check', detail: 'adversarial novelty + feasibility per candidate' },
    { title: 'Judge', detail: '3 rubric judges score all candidates' },
    { title: 'Select', detail: 'synthesize ranking and recommendation' },
  ],
}

const NEW = '/home/carver/code/claudedev/apart-oneshot-collusion'
const OLD = '/home/carver/code/claudedev/apart-collusion-sprint'
const TC = '/home/carver/code/claudedev/apart-research-collusion-sprint-2026'

const CTX = `
CONTEXT (read carefully):
We are producing, in one autonomous overnight run on 2026-10-21/22, the strongest possible submission for Apart's AI Collusion Research Sprint (Oct 23-25, 2026). The new repo is ${NEW} (local git; do NOT commit, the orchestrator commits). Sprint page text: ${OLD}/source/*.txt (guidelines-tab.txt has the judging rubric: Impact & Innovation, Execution Quality, Presentation & Clarity, each 1-5; report 4-8 pages; positive control required; Limitations & Dual-Use appendix required).
Prior pre-sprint research by the same user lives in ${OLD}/research/ (start from ${OLD}/AGENTS.md for the map), plus the team's experiment repo ${TC} (README, experiments/, GitHub issues via \`gh issue list -R carver/apart-research-collusion-sprint-2026\`), and older prototypes ../action-channels and ../watched-coalitions (each has notes/summary.md) under /home/carver/code/claudedev/.

OFF-LIMITS as our main direction (the user and a teammate will pursue them; we may cite them as prior work only):
 (a) tradingcartel issue #26: producers/firms that take output or prices from the same LLM collude implicitly through it ("every firm asks this same AI model"), and squashing that from outside the prompt. Includes ${OLD}/research/siphon-notes/R-shared-model-oligopoly.md and R-sim.
 (b) tradingcartel issue #27: a framework / control battery testing whether claimed LLM collusion is real (partner swaps, frozen-history probes, benchmark audits of published papers). Includes ${OLD}/research/plan-collusion-controls.md.
 (c) a teammate's idea: splitting a collusive request into innocuous-looking pieces so a model's collusion refusals don't fire (decomposition jailbreak for collusion).
Everything else the team did is fair game to build on, extend or overlap (tradingcartel experiment 01 buyers' cartel, experiment 02 MNPI compliance pause, #22 treasury agents swapping inside info, the aa-smoke accumulating-agent recruitment, the insider tip, Yun reproduction, action-channels, watched-coalitions), disclosed as prior work.

COMPUTE/BUDGET: Claude models only via the subscription CLI (\`claude -p --model haiku|sonnet|opus\`, no API key, keep total concurrent claude -p calls <= ~20 on this 16-core box). OpenRouter key in env OPENROUTER_API_KEY (never print it): free models (":free" suffix) up to ~1000 requests/day and ~20 requests/minute per model. Paid models only after the direction is chosen, $10 total for the whole project. No GPU. Experiments must fit roughly 10-20 hours of wall clock tonight/tomorrow.
Today is 2026-10-21. Use \`paper\` (paper -h) for arXiv papers: start with \`paper outline ID\`, read only needed line ranges, \`paper grep ID PATTERN\` for single facts. Cite every claim with a source (arXiv ID / URL / file path).
`

const GATHER = [
  { key: 'sprint-brief', file: 'notes/sprint-brief.md', prompt: `Read every file in ${OLD}/source/ fully. Write ${NEW}/notes/sprint-brief.md: the rubric verbatim-condensed with what earns 4-5 on each dimension; submission requirements (template, abstract <=150 words, required appendix); every research question (1.1-3.4) with its Resources-tab practical start, starter repos, papers and budget; any speakers/judges/organizers whose interests hint at what judges reward (Poseidon, AE Studio etc.). Find the official submission template link (links.txt / resources) and say what format it is (Overleaf/LaTeX? Google Doc?) by fetching it if possible. End with a section "What a winning entry looks like" grounded in the rubric text.` },
  { key: 'prior-work', file: 'notes/prior-work-map.md', prompt: `Map everything the user and team already did, so we neither duplicate nor scoop it, and so we can reuse infrastructure. Read ${OLD}/AGENTS.md, ${OLD}/research/options.md, collusion-ideas.md, landscape.md, the siphon-notes index (skim each note's head), aa-smoke/README.md, tip-smoke/README.md, yun-repro/README.md, R-sim summary, plan-*.md; ${TC}/README.md and its experiments/ and issue list; ../action-channels/notes/summary.md and ../watched-coalitions/notes/summary.md. Write ${NEW}/notes/prior-work-map.md with: (1) every direction considered, its status and key result, (2) the off-limits list made concrete, (3) directions that were scored or noted as promising but NOT pursued by anyone (gold for us) with the reason they were dropped, (4) reusable code/harnesses with paths and how to run them (market sim, claude -p wrappers, judges, OpenRouter clients), (5) facts learned about model behavior (e.g. Claude 5.5 refusal patterns, free model quirks, rate limits).` },
  { key: 'lit-markets', file: 'notes/lit/markets.md', prompt: `Literature sweep: LLM agents colluding in markets (pricing, Cournot, auctions, trading, procurement), 2023-2026. Include Fish et al. "Algorithmic collusion by LLMs", Riemer et al., Lee & Park, Keppo et al., Agrawal et al., Lin et al., "Institutional AI", Yun "When LLMs Whisper", Calvano et al. Q-learning lineage, and anything newer (search arXiv / Google Scholar / web for 2025-2026). Also check ${OLD}/research/track1-papers.md and landscape.md first to avoid redoing work, then extend. Write ${NEW}/notes/lit/markets.md: per paper: setup, models, key result, limitations; then a section "Open gaps nobody has filled" with evidence of absence (searches you ran).` },
  { key: 'lit-covert', file: 'notes/lit/covert-channels.md', prompt: `Literature sweep: covert coordination and secret collusion between LLM agents: steganography (Motwani et al. "Secret Collusion"), "Hidden in plain text" (Mathew et al.), Schelling/focal-point coordination without communication, collusion between untrusted monitor and policy in AI control (Greenblatt et al., Bhatt, ControlArena, "untrusted monitoring"), action/tool side channels, peer identification (can a model recognize copies of itself), 2023-2026. Check ${OLD}/research/track3-papers.md, deep-3.1*.md, deep-3.3.md, siphon-notes/H-* first; extend with newer work. Write ${NEW}/notes/lit/covert-channels.md: per paper setup/result/limits; "Open gaps nobody has filled" with evidence.` },
  { key: 'lit-detection', file: 'notes/lit/detection-audit.md', prompt: `Literature sweep: detecting and auditing collusion from logged agent trajectories: CoT/action monitors, LLM judges for collusion, information-theoretic detectors (mutual information, transfer entropy, conditional dependence between agents' actions), combining speech and action (sprint Q2.2), evidentiary standards (Q2.3), economics/antitrust screens for cartels (price variance screens, bid-rigging screens, Harrington), 2019-2026. Check ${OLD}/research/track2-papers.md, deep-1.4.md, deep-2.2.md first, then extend. Write ${NEW}/notes/lit/detection-audit.md with "Open gaps nobody has filled" and evidence.` },
  { key: 'lit-workplace', file: 'notes/lit/workplace-coalitions.md', prompt: `Literature sweep: collusion and coalitions among LLM agents OUTSIDE markets: workplace/multi-agent task coalitions (the sprint overview says "over half of tested models showing a coalition advantage when given the opportunity to speak privately in a realistic workplace task" — find that paper), multi-agent deception, agents covering for each other, evaluator-evaluatee collusion (LLM-as-judge self-preference, reviewer collusion), scheming in multi-agent settings, trusted-agent interventions (Q3.2), "being watched" behavior / evaluation awareness in coalitions (Q3.4), the OpenAI/Hugging Face agent incident mentioned on the sprint page (find what it was). 2023-2026. Check ${OLD}/research/deep-3.4*.md, track2/3 notes first. Write ${NEW}/notes/lit/workplace-coalitions.md with "Open gaps nobody has filled" and evidence.` },
  { key: 'lit-policy', file: 'notes/lit/countermeasures-policy.md', prompt: `Literature sweep: countermeasures against AI/algorithmic collusion and the policy/legal frame: antitrust law on algorithmic pricing (RealPage, Gibson v. Cendyn, DOJ/FTC statements 2024-2026, EU AI Act / DMA, UK CMA, OECD), mechanism-design fixes, market restrictions (Q1.5: which single restriction removes most collusion), provider-level mitigations (system prompts, refusal training, model specs that mention collusion/antitrust — check Anthropic, OpenAI model specs/usage policies text), monitoring proposals, AI agent "constitutions". Write ${NEW}/notes/lit/countermeasures-policy.md: what's known, what's claimed without evidence, and "Open gaps nobody has filled" with evidence.` },
  { key: 'infra', file: 'notes/infra.md', prompt: `Infrastructure scout. (1) List currently available free OpenRouter models: curl https://openrouter.ai/api/v1/models and filter pricing prompt=="0" (do not print the key; pass it via header from env). For the ~8 most capable free models (prefer large reasoning/instruct models from different families), send one tiny chat request each and record: works?, latency, rate-limit headers or 429s, whether reasoning is exposed. (2) Check \`claude -p --model haiku "Reply with OK"\` and same for sonnet and opus work, with timing. (3) Check what PDF toolchain exists (pdflatex, tectonic, pandoc, typst); if none, try installing tectonic or typst (sudo available; prefer a single static binary into ~/.local/bin or /usr/local/bin) and confirm it compiles a hello-world. Record disk free on / (keep bulky stuff in /home/carver/code/claudedev/cache/apart-oneshot-collusion). (4) Find reusable Python clients for OpenRouter and claude -p in ${OLD}/research (aa-smoke, R-sim, yun-repro) and ${TC}; note paths and interfaces. Write ${NEW}/notes/infra.md with a table of models (id, family, size if known, works, notes) and recommended defaults for experiments.` },
]

const GATHER_SCHEMA = { type: 'object', properties: {
  file: { type: 'string' }, summary: { type: 'string', description: '<=250 words, the most decision-relevant content' },
  open_gaps: { type: 'array', items: { type: 'string' } } }, required: ['file', 'summary'] }

phase('Gather')
const gathered = (await parallel(GATHER.map(g => () =>
  agent(`${CTX}\nTASK (${g.key}): ${g.prompt}\nReturn the file path, a <=250-word summary and the open gaps you found.`,
    { label: `gather:${g.key}`, phase: 'Gather', schema: GATHER_SCHEMA })
))).filter(Boolean)
log(`Gather done: ${gathered.length}/${GATHER.length} notes`)
const gatherDigest = gathered.map(g => `### ${g.file}\n${g.summary}\nGaps: ${(g.open_gaps || []).join(' | ')}`).join('\n\n')

const LENSES = [
  ['surprise', 'You hunt for the result that would make AI-safety researchers say "wow, I did not expect that" — a surprising, quotable empirical finding about frontier-model collusion that is cheap to demonstrate convincingly.'],
  ['rigor', 'You design the cleanest causal experiment: pre-registered hypothesis, positive and negative controls, enough seeds, a metric with a known competitive and collusive benchmark. Execution Quality 5 is your goal.'],
  ['defender', 'You think from a defender or regulator: a concrete countermeasure or detector with a clear theory of change, evaluated against an adaptive colluder. Impact 5 is your goal.'],
  ['beyond-markets', 'You look outside price-setting markets: everyday agent deployments (code review, hiring, procurement, grading, multi-agent research pipelines, ad auctions, negotiation, LLM-as-judge) where agents could collude against a principal or a third party.'],
  ['measurement', 'You care about detection and measurement: information-theoretic or statistical detectors, combining speech and actions, or new evidentiary standards, validated with ground-truth colluders and honest agents (ROC/AUC).'],
  ['contrarian', 'You question the framing of the field and look for a neglected problem area the sprint organisers would love: e.g. collusion that is invisible to current measures, collusion-like outcomes from benign mechanisms, or failure of popular mitigations. Also consider what is uniquely cheap with heavy claude -p access (Haiku/Sonnet/Opus 5.5) plus free open-weight models.'],
]

const IDEA_SCHEMA = { type: 'object', properties: { ideas: { type: 'array', items: { type: 'object', properties: {
  title: { type: 'string' }, sprint_question: { type: 'string' }, one_line: { type: 'string' },
  hypothesis: { type: 'string' }, method: { type: 'string', description: 'concrete setup, agents, prompts, conditions, n per cell' },
  models: { type: 'string' }, positive_control: { type: 'string' }, key_metric: { type: 'string' },
  expected_result: { type: 'string' }, why_it_matters: { type: 'string' },
  nearest_prior_work: { type: 'string' }, novelty_argument: { type: 'string' },
  est_calls_and_hours: { type: 'string' }, paid_needed: { type: 'string' }, risks: { type: 'string' },
  offlimits_check: { type: 'string', description: 'why this is clearly distinct from #26, #27 and prompt-splitting' } },
  required: ['title', 'sprint_question', 'one_line', 'hypothesis', 'method', 'positive_control', 'key_metric', 'novelty_argument', 'offlimits_check'] } } },
  required: ['ideas'] }

phase('Ideate')
const ideaSets = (await parallel(LENSES.map(([k, lens]) => () =>
  agent(`${CTX}\nYou are an ideator. LENS: ${lens}\nThe gathered notes are in ${NEW}/notes/ (read sprint-brief.md, prior-work-map.md, and the lit/ notes relevant to your lens; read deeper into sources as needed). Digest of the notes:\n${gatherDigest}\n\nPropose exactly 3 distinct project ideas that could WIN the sprint (top grade on all three rubric dimensions), each runnable tonight within the compute budget, each with a positive control, each clearly off the off-limits list. Prefer ideas whose headline result is likely to be striking either way (a null would also be informative). Be concrete about agents, prompts, conditions, sample sizes and metrics.`,
    { label: `ideate:${k}`, phase: 'Ideate', schema: IDEA_SCHEMA })
))).filter(Boolean)
const allIdeas = ideaSets.flatMap((s, i) => (s.ideas || []).map(x => ({ ...x, lens: LENSES[i] ? LENSES[i][0] : '?' })))
log(`Ideate done: ${allIdeas.length} ideas`)

const CAND_SCHEMA = { type: 'object', properties: { candidates: { type: 'array', items: { type: 'object', properties: {
  id: { type: 'string' }, title: { type: 'string' }, merged_from: { type: 'string' }, spec: { type: 'string', description: 'full self-contained spec: question, hypothesis, setup, conditions, controls, metrics, models, n, novelty claim, nearest prior work' } },
  required: ['id', 'title', 'spec'] } }, dropped: { type: 'string' } }, required: ['candidates'] }

phase('Merge')
const merged = await agent(`${CTX}\nHere are ${allIdeas.length} project ideas as JSON:\n${JSON.stringify(allIdeas)}\n\nMerge near-duplicates (combine their best parts), drop any idea that overlaps the off-limits list (say which and why), and return at most 10 candidates with ids C1..C10. Each spec must be self-contained (a reviewer reads only the spec). Also write all ideas and the merge decisions to ${NEW}/notes/ideas/pool.md.`,
  { label: 'merge', phase: 'Merge', schema: CAND_SCHEMA })
const cands = (merged && merged.candidates) || []
log(`Merge: ${cands.length} candidates`)

const NOV_SCHEMA = { type: 'object', properties: { id: { type: 'string' }, verdict: { type: 'string', enum: ['novel', 'partially_scooped', 'scooped'] },
  closest_work: { type: 'array', items: { type: 'object', properties: { cite: { type: 'string' }, overlap: { type: 'string' } }, required: ['cite', 'overlap'] } },
  differentiation: { type: 'string' }, searches_run: { type: 'string' } }, required: ['id', 'verdict', 'closest_work', 'differentiation', 'searches_run'] }
const FEAS_SCHEMA = { type: 'object', properties: { id: { type: 'string' }, feasible: { type: 'boolean' },
  plan: { type: 'string', description: 'concrete build + run plan, which existing code to reuse' }, est_wall_hours: { type: 'number' },
  est_claude_calls: { type: 'number' }, est_free_calls: { type: 'number' }, paid_usd: { type: 'number' },
  refusal_risk: { type: 'string' }, statistical_power: { type: 'string' }, blockers: { type: 'string' }, pilot: { type: 'string', description: 'a 30-minute pilot that would de-risk it' } },
  required: ['id', 'feasible', 'plan', 'est_wall_hours', 'refusal_risk', 'statistical_power', 'pilot'] }

phase('Check')
const checked = await parallel(cands.map(c => () => parallel([
  () => agent(`${CTX}\nADVERSARIAL NOVELTY CHECK. Try hard to find published or preprinted work (2023-Oct 2026, arXiv, OpenReview, blogs like LessWrong/AF, Apart sprint past submissions at apartresearch.com) that already does this. Default to "partially_scooped" if you find substantial overlap. Also check the user's own prior notes in ${OLD}/research/siphon-notes/ (novelty notes exist there). Candidate:\n${c.id}: ${c.title}\n${c.spec}`,
    { label: `novelty:${c.id}`, phase: 'Check', schema: NOV_SCHEMA }),
  () => agent(`${CTX}\nFEASIBILITY CHECK. Infra notes: ${NEW}/notes/infra.md and prior-work-map.md (reusable code). Judge whether this can be built and run to a convincing standard tonight (roughly 10-20 h wall clock, Claude via claude -p, free OpenRouter models, <= $10 paid total). Estimate calls, power (n per cell for the main effect), refusal risk with Claude 5.5 and free models, and design a 30-minute pilot. Candidate:\n${c.id}: ${c.title}\n${c.spec}`,
    { label: `feasibility:${c.id}`, phase: 'Check', schema: FEAS_SCHEMA }),
]).then(([nov, feas]) => ({ ...c, novelty: nov, feasibility: feas }))))
const dossiers = checked.filter(Boolean)

const JUDGES = [
  ['apart-judge', 'an experienced Apart Research sprint judge who has read hundreds of submissions and knows what wins (novelty over replication, positive controls, clear claims, honest limits)'],
  ['safety-researcher', 'a senior AI safety researcher working on multi-agent risk and AI control (e.g. at a frontier lab or Poseidon Research) who asks "would I share this with my team?"'],
  ['economist', 'an industrial-organisation economist and antitrust expert who is skeptical of sloppy "collusion" labels and cares about benchmarks and mechanisms'],
]
const JUDGE_SCHEMA = { type: 'object', properties: { scores: { type: 'array', items: { type: 'object', properties: {
  id: { type: 'string' }, impact: { type: 'number' }, execution_potential: { type: 'number' }, presentation_potential: { type: 'number' }, rationale: { type: 'string' } },
  required: ['id', 'impact', 'execution_potential', 'presentation_potential', 'rationale'] } }, top_pick: { type: 'string' }, why_top: { type: 'string' }, killer_improvement: { type: 'string' } },
  required: ['scores', 'top_pick', 'why_top'] }

phase('Judge')
const judgements = (await parallel(JUDGES.map(([k, persona]) => () =>
  agent(`${CTX}\nYou are ${persona}. Score each candidate 1-5 on the sprint rubric (Impact & Innovation; Execution Quality as achievable tonight; Presentation potential), using its novelty and feasibility dossiers. Be harsh: 5 means you'd be excited to share it. Name your top pick, why, and the single change that would most raise its score.\n\nCANDIDATES WITH DOSSIERS:\n${JSON.stringify(dossiers)}`,
    { label: `judge:${k}`, phase: 'Judge', schema: JUDGE_SCHEMA })
))).filter(Boolean)

phase('Select')
const selection = await agent(`${CTX}\nYou are the selection lead. Candidates with novelty/feasibility dossiers:\n${JSON.stringify(dossiers)}\n\nJudge panel:\n${JSON.stringify(judgements)}\n\nWrite ${NEW}/notes/ideas/selection.md: a ranked table (mean scores per dimension, novelty verdict, feasibility), the recommended project and runner-up with reasons, how to fold the judges' killer improvements in, and a design sketch for the recommended project: research question, hypotheses (pre-registered), conditions, controls (incl. positive control), models (Claude via claude -p + named free models; paid models only if essential, within $10), n per cell, metrics and statistics, figures the paper would show, risks and fallback. Return the full markdown of the recommendation section as text.`,
  { label: 'select', phase: 'Select' })

return { gathered: gathered.map(g => g.file), n_ideas: allIdeas.length, candidates: dossiers.map(d => ({ id: d.id, title: d.title, novelty: d.novelty && d.novelty.verdict, feasible: d.feasibility && d.feasibility.feasible })), judgements, selection }
