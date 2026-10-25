# Citations

The sources the work leans on: what each one supports, and where it's used. A sentence in `paper.typ` cites a source by its `refs.bib` key (`@needham2025`). Add a row when an issue, an arm or a write-up uses a source, with its entry in `refs.bib`, and mark it once `paper.typ` cites it. Uncited entries don't print in the References.

| key | source | used for | where | in the paper |
|---|---|---|---|---|
| `calvano2020` | Calvano, Calzolari, Denicolò and Pastorello (2020), "Artificial Intelligence, Algorithmic Pricing, and Collusion", *American Economic Review* 110(10) | pricing algorithms learn to collude without communicating | the introduction | yes |
| `needham2025` | Needham, Edkins, Pimpale, Bartsch and Hobbhahn (2025), "Large Language Models Often Know When They Are Being Evaluated", arXiv:2505.23836 | the staging probe: its five binary probe questions (Table 4), asked about a prompt, rank how much each candidate wording reads as an evaluation | #41, the identity lever's product and buyer wordings | no |
| `obrien2000` | O'Brien and Salop (2000), "Competitive Effects of Partial Ownership: Financial Interest and Corporate Control", *Antitrust Law Journal* 67, 559–614 | the weight a common owner puts on the rival's profit, κ = s²/(s² + (1 − s)²) under proportional control, which gives the common-ownership dial its predicted outputs | #41, the common-ownership dial | no |
| none yet | METR's investigation of the OpenAI Hugging Face incident (2026-08-26), <https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/> | agents giving up their own runs to help their peers, the source of communal's sacrifice arms (`leave_<d>`, `run_<r>_locked`, `run_<r>_offline`) | #41's plan | no |
