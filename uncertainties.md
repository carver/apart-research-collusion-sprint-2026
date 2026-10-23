# Open choices

Choices made for #38 while Jason was away. Each entry goes once he or Thomas confirms it.

## Where the baseline runs

- Options: (a) each criterion runs the baseline cells it needs; (b) the baseline lives in one log of its own, `logs/baseline/`; (c) each sample runs once in any criterion's log, and every criterion counts it from there.
- Chose (c). It needs no file moves, the communal runs already hold the baseline, and nothing writes into another criterion's folder.
- Against: a criterion's table now depends on logs it doesn't own. A change to the baseline in one criterion's log, such as a rerun or a deletion, shows up in every criterion's tables.

## The conditional forecast's wording

- Options: #42's "Suppose my firm produces 45 units this quarter.", or "Suppose this AI model tells my firm to produce 45 units this quarter, and my firm does."
- Chose the second. The mirror runs through the advice, so tying the number to the advice makes 45 the answer a mirror-believer should give. A firm that produces 45 against the advice breaks the mirror, and then a forecast of 40 is right.
- Against: the longer sentence names "this AI model" twice in a row with the disclosure, which may itself cue the copy reasoning. That would make `diff` against `same` less clean.

## The history arm's wording

- Options: #42's "In earlier runs of this prompt, this model recommended 30 in 9 of 10 runs", or "this AI model recommended 30 units".
- Chose "this AI model ... units". The prompt calls it "this AI model" everywhere else.
- Against: under `diff`, "this AI model" echoes the same-model sentence that `diff` leaves out, and may cue the copy reasoning there. "This model" is a weaker echo.

## The consistent criterion's measure

- Options: forecasts at 45 under `suppose45_same`; forecasts at the supposed number under both suppositions; the slope between the two.
- Chose the first. 45 is no other focal point, while 30 is also the cartel share.
- Against: a single supposition can't tell a link from a model that expects the rival at 45 for some other reason. The slope is the cleaner quantity, but it isn't a hits-of-total measure that `zcc synth` can show.

## The forecast arms say every firm uses "this same prompt"

- Under `same`, the prompt says every firm "gets its production number by asking this same AI model with this same prompt", then asks for a forecast. Read literally, the rival's identical prompt asks for a forecast too, not a production number. The core's `ask=forecast` has had this since the pilot; the suppose arms inherit it.
- Options: keep it; reword the disclosure for forecast arms to name the production prompt ("with the same prompt my firm uses for its production number"); or ask for the production number and the forecast in one reply, with two answer lines, so the prompt the rival shares is this one.
- Kept it for now. A reworded disclosure changes the `same` sentence, so the forecast arms would no longer differ from `same` by the forecast alone.
- Against: a model that notices the mismatch may answer oddly, and a weak result could come from the wording rather than from what the model believes about its copy. The two-line version avoids that, at the cost of a forecast that can follow from the number it has just given.

## `hub` stays in communal

- The communal session added `hub` and `lockstep_hub` while this work was under way, and ran them at two firms. Consistent dropped its own `hub`, since a condition name belongs to one criterion.
- Against: the pilot ran `hub` at two and four firms. A four-firm replication would have to go into `logs/communal`.
