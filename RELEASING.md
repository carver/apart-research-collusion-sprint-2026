# Releasing

A release here exists so people can cite the repository. Zenodo archives each GitHub release and
gives it a DOI, reading the authors, title, version and license from `CITATION.cff`. `bin/release`
does the repository side. The Zenodo side is two manual steps, both only needed around the first
release.

## Before the first release: keep the road to a paper open

The sprint ends in a report. The day it is public (arXiv, or Apart's site), add a
`preferred-citation:` block with `type: article` to `CITATION.cff`, and GitHub's cite button then
shows the report. The software DOI stays valid and the report cites it. Citations made to the
software DOI before then do not move to the report, so add the block as soon as the report exists.

Do these before the first DOI exists.

- [x] Jason's ORCID is in `CITATION.cff`.
- [ ] Thomas registers an ORCID at orcid.org, and it goes under his entry in `CITATION.cff` as
      `orcid: "https://orcid.org/0000-0000-0000-0000"`, replacing the TODO comment there. It ties
      the same person together across Zenodo, arXiv and a venue.
- [ ] Keep one name form everywhere. `CITATION.cff` and `REUSE.toml` say "Thomas Redfern", but his
      git commits say "Thomas". `git config user.name "Thomas Redfern"` fixes the commits from then
      on.
- [x] License so a report can reuse the prose. Since 2026-10-23 the prose, notes, reports, data
      and run logs are CC-BY-4.0 and the code is MIT (`REUSE.toml` maps paths to licenses). A
      contribution comes in under the license of the files it touches.
- [ ] Decide when to release. At the least, release when the sprint report is submitted, so it can
      cite the exact version behind its tables, then again at each later results milestone.
- [ ] Double-blind venues. A public repository with your names and a DOI deanonymizes a
      submission. arXiv and most ML venues do not mind, and anonymized mirrors exist for the ones
      that do. Pick the kind of venue before the DOI spreads.
- [x] Run data. The runs are committed under `logs/`, so each release archive holds them.
      `bin/release` refuses while a logs commit is held back for review (see "Every release").

## Once, before the first release

Zenodo archives only releases created after the repository is switched on. A release cut before
that gets no DOI, and Zenodo does not pick it up later.

1. Log in at zenodo.org with the GitHub account that owns the repository (`carver`). Zenodo
   installs a webhook, so the account needs admin rights on it.
2. Open https://zenodo.org/account/settings/github, press "Sync now" if the repository is missing,
   and flip its switch on.

`bin/release` cannot check this switch. The sandbox token gets a 404 from GitHub's webhook API.
So the first release takes `--zenodo-enabled`, which is you saying the switch is on.

## Every release

Run on main, with `gh` (logged in to GitHub) and `uvx` (part of uv) installed. The tool checks
both are on the PATH before it changes anything.

    bin/release v0.1.0 --dry-run --zenodo-enabled   # checks, then prints the plan
    bin/release v0.1.0 --zenodo-enabled             # the first release
    bin/release v0.2.0                              # later ones, once the cff has a doi

The tool writes the version and today's date into `CITATION.cff`, validates the file, commits it
alone, tags the commit, pushes main with the tag and creates the GitHub release with generated
notes. Pick the version by hand. Nothing here depends on semver meaning, so bump the minor number
when the findings change and the patch number for fixes. Uncommitted work in the tree stays out of
the release commit, staged or not.

The tool refuses, before changing anything, when the version is not `vX.Y.Z`, the tag already
exists here or on origin, the branch is not main, `CITATION.cff` has uncommitted edits or lists
several licenses, origin/main has commits this clone lacks, or main has commits origin/main lacks.

The last check is there because the push would publish those commits. AGENTS.md holds a logs
commit back until Jason or Thomas have reviewed it, and the commits after it wait too. Push the
commits that are ready. While a held-back logs commit is on main, the release waits for its review.

## Once, after the first release

Zenodo takes a few minutes. The repository's row at https://zenodo.org/account/settings/github
then shows the release with a DOI badge. If it shows an error instead, one known cause is a
`CITATION.cff` Zenodo could not parse, which the tool's validation step should have caught.

The record page lists two DOIs. One names this version. The other, under "Cite all versions",
always resolves to the latest. Put the second one in `CITATION.cff` as a top-level line:

    doi: 10.5281/zenodo.NNNNNNN

Then update the "How to cite" section of the README, which still says there is no DOI, and add
the badge Zenodo offers on the record page. Commit both on main. The DOI reaches the cff one
release late by design, since Zenodo mints it only after the release exists.

From then on the `doi` line tells `bin/release` that Zenodo works, and the flag is not needed.

## When a step fails

Everything up to validation leaves the tree as it was. After that the tool runs four commands in
order: commit, tag, push, create the release. If one fails it stops and prints the commands still
to run. Fix the cause and run those by hand. Do not rerun `bin/release` with the same version. It
will refuse, because the tag now exists.

To abandon a release that failed before the push, delete the tag with `git tag -d vX.Y.Z` and
revert the release commit. After the push, cut the next patch version instead. Zenodo records are
permanent, and a tag other people may have fetched should stay where it is.
