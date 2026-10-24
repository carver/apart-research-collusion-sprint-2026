# Submission requirements: AI Collusion Research Sprint (fetched 2026-10-23)

Everything below was fetched on 2026-10-23, about 20:55 PDT (2026-10-24 04:00 UTC), and supersedes the 2026-10-21 note from Jason's earlier run (apart-oneshot-collusion, `paper/template/requirements.md`). Fetch the pages again before submitting: the rules changed during the last sprint.

Sources (the page text is quoted below; the downloads weren't committed):

- The sprint page's Guidelines tab: https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25#guidelines
- The submission form (the "Submit your project" button on the same page opens it)
- The official template, the Google Doc the Guidelines tab links twice ("official template" and "Submission Template => Link"): https://docs.google.com/document/d/1Y5wd3VRbXU5N08BvAGiJUQTaWbMCSPjhzXsR-ozuehg/copy?usp=sharing, read through its `/export?format=pdf`, `docx` and `txt` exports
- The rubric page the template links ("Evaluation Rubric"): https://apartresearch.notion.site/sprint-evaluation-rubric, with its "Reviewer Guidance" and "Flags" toggles opened

The template link has the same document ID as on 2026-10-21. The Overview and Resources tabs say nothing about the report beyond "write up what you found", plus the Resources tab's planning advice ("Start with 3 to 5 seeds per condition and expand to 10 to 20 only after the positive control works."). The prize-terms page linked from the form covers only prize payments.

## 1. Page cap and what it excludes

- Guidelines, Required: "Maximum 8 pages, not counting references and appendices."
- Guidelines, Recommended Report Structure: "Most strong projects are 4 to 8 pages. The cap is 8 pages, not counting references and appendices."
- Pre-submission checklist: "8 pages or fewer before references and appendices".
- Template info box: "Recommended length: 4 pages excluding references and appendix. Rough guide: Intro & Related Work 1p, Methods and Results: 2.5p, Discussion 0.5p."
- Rubric, Reviewer Guidance: "Quality over quantity: A focused 4-page submission often beats a noisy 10-page one." and "Verbosity that obscures substance → subtract from Presentation".

So the counted pages run from page 1 (title block and abstract included; nothing says otherwise) to the start of References. Nothing says whether "Code and Data" and "Author Contributions", which the template puts before References, are excluded, so count them. The template puts the "LLM Usage Statement" after the Appendix, so it falls outside the cap with the appendices, but no rule says so outright.

## 2. Abstract

- Guidelines, Required: "Project title and abstract, 150 to 250 words."
- Checklist: "abstract 150 to 250 words".
- Template: "Summarize your project in 150–250 words. A strong abstract lets a reviewer understand what you did and why it matters without reading anything else. Make sure to cover: the problem, your approach, key results, and the main takeaway. Polish it last: the abstract should reflect your final results, not your initial plan."
- The submission form also asks for a "Project summary *": "A short abstract: what you did, what you found." (no word count given).

## 3. Required content, sections and appendices

Guidelines, Required:
> Research report (PDF) using the official template.
> Maximum 8 pages, not counting references and appendices.
> Project title and abstract, 150 to 250 words.
> Author names and affiliations.
> A "Limitations and Dual-Use / Ethical Considerations" appendix (required, see below).

Guidelines, Recommended Report Structure (in this order):
> Introduction: the question and why it matters.
> Related Work: what you build on (see Resources).
> Methodology: enough detail to replicate (models, prompts, environments, seeds, metrics).
> Results: quantitative where possible; report variance, seeds and baselines, and always include the positive control.
> Discussion: implications, limitations, and future work.
> Limitations and Dual-Use / Ethical Considerations (required): state what your result does and does not establish, and note any way your setup or findings could make real-world collusion easier to carry out or harder to detect.
> References.

Template headings, in order (numbered ones carry the number in the heading text):
1. `1. Introduction`, ending with "**Our main contributions are:**" and a numbered list "1. [First contribution — what new thing did you create, discover, or demonstrate?] 2. [Second contribution] 3. [Third contribution, if applicable]"
2. `2. Related Work`
3. `3. Methods`
4. `4. Results`: "we strongly encourage at least one figure"; "Distinguish between observations and interpretations."; "Do you have enough data? Is the difference statistically significant?" and "Is it robust? Or do small changes to your setup cause substantial changes to your results?"
5. `5. Discussion and Limitations`, with unnumbered subsections `Limitations` and `Future Work`
6. `6. Conclusion`: "Briefly summarize your main findings and their implications (1–2 paragraphs)."
7. `Code and Data` (unnumbered)
8. `Author Contributions (optional)` (unnumbered)
9. `References` (unnumbered): "Use a consistent citation format. Include: Author(s), Year, Title, Venue/Publisher, and URL or DOI where available." The placeholder is a numbered list "1. [Reference 1]".
10. `Appendix (optional)` (unnumbered): "Supplementary material such as additional figures, detailed methodology, prompts used, extended results, etc."
11. `LLM Usage Statement` (unnumbered; see §4)

The template says "The section structure is strong guidance but not rigid. If your project requires a different organization, feel free to adapt." and "Delete all guidance text including this info box before submitting."

**Conflict**: the template has no "Limitations and Dual-Use / Ethical Considerations" appendix, yet the Guidelines require one, and the checklist calls it the "Limitations and Dual-Use / Ethical appendix". Keep the template's §5 Limitations subsection and add an appendix with exactly that title.

Figures and tables (template, "Tips for figures and tables"):
> Number all figures (Figure 1, Figure 2...) and tables (Table 1, Table 2...)
> Include descriptive captions that can be understood without the main text
> Place figures/tables near where they're first referenced
> Ensure text in figures is legible!

The template contains no example figure or table, so it sets no caption style (position, size, label format) beyond "Figure N" / "Table N" numbering.

Citations (FAQ): "Do you require a particular citation style? No. Use whichever style you are comfortable with and stay consistent."

Template: "Always use the one linked on the Guidelines tab. The template in any acceptance email may be older." (FAQ, "Which template should I use?")

## 4. AI use and AI writing

Guidelines, section "AI tools and your report" (exact):
> Use AI tools however they help you: to check your reasoning, find gaps in a draft, write and debug code, or help with the writing. Your team is responsible for everything in the report, and made-up results or references can disqualify a project. Judges score each report on the rubric, and a judge can decline to score one too unclear to follow.

FAQ, "Can I use AI tools?" (exact):
> Yes: use AI tools however they help you. Your team is responsible for everything in the report, and made-up results or references can disqualify a project. Judges score each report on the rubric, and a judge can decline to score one too unclear to follow.

Template, `LLM Usage Statement` section (exact):
> If you used LLM assistance in developing your project or writing this report, briefly note how. Ensure all claims and results have been verified.
>
> NOTE: We strongly encourage that the final version of the submission is primarily written by your team.
>
> [e.g., "We used Claude to brainstorm approaches and help draft sections. All results and claims were independently verified."]

So AI help with the writing is allowed. Fabricated results or references can disqualify a project. The template asks for an LLM Usage Statement and "strongly encourage[s]" human-primary writing, which is advice, not a rule.

## 5. Prior work disclosure

Guidelines, Important Notes, and the FAQ "Can I build on existing research?" (same wording):
> Building on existing work is allowed and encouraged, but you must clearly identify what is new work done during the sprint. Undisclosed prior work can lead to disqualification. Mark any code you wrote before the sprint as preexisting in the README and the report.

The template has no slot for this. The rule needs it in both the README and the report.

## 6. Title block and footnote (template)

- A top rule (3 pt, a table-cell border), then the title centred, Old Standard TT 20 pt bold (placeholder typed in capitals, "PROJECT TITLE"; the Title style itself does not force caps), then a 1 pt rule.
- Footnote marker "1", superscript, on the title. Footnote text in Old Standard TT 10 pt: "Research conducted at the AI Collusion Research Sprint, October 2026", with "AI Collusion Research Sprint" a blue (#1155cc) underlined link to https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25.
- Authors: a centred table about 5 in wide, three per row (six placeholder slots), each cell "Author name N" line break "Affiliation", 11 pt regular, centred.
- Below it, centred: "**With**" (bold) line break "Apart Research" (regular).
- "Abstract" heading: 14 pt bold, centred, 12 pt before, 10 pt after.
- Abstract body: justified, inset (text starts 0.99 in from the left margin, ends about 1.13 in from the right), 11 pt, italic in the template.
- A yellow (#fff2cc) Arial 12 pt info box, to be deleted before submitting.

## 7. Layout (template docx and PDF)

- US Letter (12240 x 15840 twips; PDF 612 x 792 pt), portrait, 1 in margins on all sides (header/footer distance 0.5 in), single column.
- No header, footer or page numbers (no footer reference; `pgNumType start=1` only).
- Font: Old Standard TT throughout the content (Regular, Bold, Italic embedded in the docx). The doc default is Arial, which shows only in the info box and the list markers.
- Body 11 pt, line spacing 1.15 (docDefault `line=276`), left-aligned (not justified), no space after paragraphs (blank paragraphs separate them).
- Section headings ("1. Introduction" and the unnumbered "Code and Data", "References", etc.): Old Standard TT 14 pt bold, **black** (Heading2 style, no colour set), 10 pt before, 0 after, 1.5 line spacing, keep-with-next.
- Subsection headings ("Limitations", "Future Work"): Old Standard TT 13 pt bold, **black** (#000000, which overrides Heading3's #434343), 10 pt before, 4 pt after.
- Lists: decimal "1." (contributions, references), "(a)" lower-letter (guidance questions), "-" bullets (Code and Data links, figure tips), indented 0.5 in with a 0.25 in hanging indent.
- Footnotes 10 pt.
- Links #1155cc, underlined.

## 8. Code, data, video and other submission fields

- Guidelines, Optional: "Public GitHub repo." and "A 3 to 5 minute video demo."
- Template `Code and Data`: "Include links if applicable. If your project doesn't involve code (e.g., policy analysis) or if there are info-hazard considerations, note that here." with bullets "**Code repository**: [Link to GitHub/GitLab if applicable]", "**Data/Datasets**: [Link if applicable]", "**Other artifacts** (optional): [Demo link, video walkthrough, Hugging Face Space, etc.]"
- Checklist ends with "links work."
- Submission form: required "Project title", "Project summary" ("A short abstract: what you did, what you found."), "PDF report" ("PDF, up to 25 MB. Check it's the final version before you submit."), "Are you interested in publishing this project?", "Team name", "Location", and per member "Name" and "Email". Optional: "Tracks", "Presentation recording", "Project code", "Slides" (PDF, PowerPoint, Keynote or ODP, up to 25 MB), "Project image" (PNG, JPEG, WebP or GIF, up to 25 MB), "Additional material", "Discord username", "Google Scholar profile".
- Fixing a submission (Important Notes, exact): "Fixing or resubmitting: if a detail in the form is wrong (a missing team member, a wrong email), submit the form again with the same title and the record updates. The PDF itself is not replaced: to change it, make a new submission with a slightly different title, or email the new PDF to sprints@apartresearch.com. Do this before the deadline. Projects go to the judges a few hours after it, and we remove the superseded entry."
- Deadline: "Submissions close Oct 25, 2026 at 11:59 PM Anywhere on Earth."
- Projects per person: "each person can be on at most two projects."
- Rubric Flags: "Off-topic: Project does not fit any track for the current hackathon." Such projects "are excluded from hackathon prizes".

## 9. Rules a build script can check

| Check | Source |
|---|---|
| Pages before the `References` heading ≤ 8 (title page counts) | Guidelines, checklist |
| Abstract 150–250 words | Guidelines, template, checklist |
| An appendix titled exactly "Limitations and Dual-Use / Ethical Considerations", after References | Guidelines |
| Title, ≥1 author with affiliation, "With Apart Research", title footnote with the sprint link | Guidelines, template |
| Section headings present in template order: Introduction, Related Work, Methods, Results, Discussion and Limitations, Conclusion, Code and Data, References; an LLM Usage Statement | Template (guidance, "not rigid") |
| A numbered contributions list in the Introduction | Template |
| ≥1 figure; every figure and table numbered and captioned; each referenced in the text | Template tips ("strongly encourage") |
| Results mention variance, seeds, baselines and a positive control | Guidelines |
| A statement marking preexisting code as preexisting | Guidelines (prior work) |
| No template guidance text or info box left in the PDF; no TODO markers | Template |
| Every reference resolves (no invented references); every URL in the PDF returns 2xx/3xx | Guidelines (AI rule), checklist "links work" |
| PDF ≤ 25 MB | Submission form |
| US Letter, 1 in margins, Old Standard TT embedded, body 11 pt, no page numbers | Template |

## 10. What bin/build-paper checks, and how paper/apart.typ follows the template

`bin/build-paper` checks, on every build: pages before References, the abstract's length, the required sections (Code and Data, LLM Usage Statement, and the Limitations and Dual-Use appendix), every figure and table referenced, no TODO markers, every number from the ledger, and the PDF's size. `--final` also checks every URL in the PDF. The other rows of §9 are for the reviewers.

`paper/apart.typ` began as the earlier run's clone of the template (preexisting) and now follows the live one: black headings and subheadings, an italic abstract, "-" bullets. Its paragraph and heading spacing approximate the template's blank 1.15-spaced lines. Its caption and table styling (10 pt captions, table captions on top, 9 pt table text) and its lettered appendices are its own choices, which the template neither shows nor forbids. `paper.typ` supplies the sections the template lacks: the Limitations and Dual-Use appendix and the LLM Usage Statement.

## Changed since 2026-10-21

Live changes (compared with the 2026-10-21 template files and a copy of the Guidelines tab saved on 2026-10-22, both from Jason's earlier runs):

1. **Resubmitting no longer replaces the PDF.** Old rule: "submit again before the deadline using the exact same title and details; your new files replace the old ones." New rule: same title updates only the form details; to change the PDF, "make a new submission with a slightly different title, or email the new PDF to sprints@apartresearch.com", before the deadline, and "we remove the superseded entry". The FAQ answer changed the same way. This changed after 2026-10-22 15:19 PDT, when the saved copy still had the old wording.
2. **Template restyled, text unchanged.** The body guidance text is no longer italic (the abstract placeholder still is). Section headings changed from dark grey #434343 to black, and the Limitations / Future Work subheadings from #666666 to black. Page size, margins, fonts, sizes, title block, footnote, section list and order, and every word of guidance are the same as on 2026-10-21. Only the line wrapping differs, because upright text is narrower.
3. Nothing else on the Guidelines tab changed: the judging criteria, required items, page cap, abstract length, recommended structure, AI-tools text, prior-work rule and checklist match the 2026-10-22 copy word for word.

Present on 2026-10-21 but missing from the old note (not live changes):

- The AI-tools rule (§4), including "made-up results or references can disqualify a project", and the template's **LLM Usage Statement** section with its "primarily written by your team" note.
- The template's **Author Contributions (optional)** section, and the order Code and Data → Author Contributions → References → Appendix → LLM Usage Statement.
- The prior-work rule: "Mark any code you wrote before the sprint as preexisting in the README and the report."
- "Links work" in the checklist; the 25 MB PDF limit and the "Project summary" field on the submission form.
- The old note said Results need "at least one figure". The template only "strongly encourage[s]" one.
- The old note gave the layout as body 11 pt and title 20 pt only. The heading colours it implied (via apart.typ) are now out of date (above).
