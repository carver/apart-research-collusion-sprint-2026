// What paper.typ imports: the template with the draft marks applied, and the numbers, tables,
// figures and texts of the ledger (build/numbers.json, which bin/build-paper writes before it
// compiles). Keys are the ledger's; README.md lists the functions.

#import "apart.typ" as template
#import "apart.typ": appendix, unnumbered

#let draft = sys.inputs.at("draft", default: "true") != "false"
#let apart = template.apart.with(
  draft: draft,
  stamp: sys.inputs.at("stamp", default: ""),
  commit: sys.inputs.at("commit", default: ""),
)
#let ledger = json("build/numbers.json")


// Red, so nothing unfinished goes unseen in a draft.
#let flag(body) = text(fill: rgb("#c00000"), weight: "bold", body)

// A key the ledger lacks, or holds as the wrong kind: marked in red, and reported by the build.
#let missing(key, why: "not in the ledger") = [#metadata((key: key, why: why)) <missing>#flag[[#key?]]]

// The ledger's entry under key when it is one of these kinds, else none.
#let entry(key, ..kinds) = {
  let e = ledger.at(key, default: none)
  if e != none and e.kind in kinds.pos() { e }
}

// A share as a whole percent, rounded half up.
#let percent(x) = str(int(calc.floor(x * 100 + 0.5))) + "%"

// A count ("43/48"), from one cell or pooled across cells, or a plain value as the ledger holds it.
#let n(key) = {
  let e = entry(key, "rate", "pooled", "value")
  if e == none { missing(key) } else if e.kind == "value" { [#e.value] } else [#e.k/#e.n]
}

// A count as a percent ("90%").
#let pct(key) = {
  let e = entry(key, "rate", "pooled")
  if e == none { missing(key) } else { percent(e.rate) }
}

// One cell's rate as a percent with its 95% Wilson interval ("90% (78–96%)"). A count pooled
// across cells (models, market sizes, prompts) has no interval.
#let ci(key) = {
  let e = entry(key, "rate")
  if e != none [#percent(e.rate) (#percent(e.lo).trim("%")–#percent(e.hi))] else if entry(key, "pooled") != none {
    missing(key, why: "pooled across cells, so it has no interval")
  } else { missing(key) }
}

// A sentence whose wording depends on the data ("most", "fell", "every model"). `test` gets the
// rate (or value) of each key in `keys`, in order, and says whether the numbers still support
// the wording. The build reports a failing claim, and one whose keys the ledger lacks; a draft
// also marks it in red.
#let claim(text, keys, test) = {
  let entries = keys.map(key => entry(key, "rate", "pooled", "value"))
  let ok = if none in entries { none } else {
    test(..entries.map(e => if e.kind == "value" { e.value } else { e.rate }))
  }
  [#metadata((ok: ok, text: text)) <claim>]
  if draft and ok != true { flag[[claim #if ok == none [can't be checked] else [fails]: #text]] }
}

// Something still to write. The build counts them; --final refuses any.
#let todo(body) = [#metadata(none) <todo>#flag[[TODO: #body]]]

// A table of the ledger's rows, styled by the template: the first column left-aligned, the rest
// centred. Extra named arguments (align, columns) go to table().
#let data-table(key, ..args) = {
  let e = entry(key, "table")
  if e == none { missing(key) } else {
    let named = (columns: e.header.len(), align: (x, _) => if x == 0 { left } else { center }) + args.named()
    table(..named, table.header(..e.header.map(h => strong(h))), ..e.rows.flatten())
  }
}

// A figure the build drew from the ledger. Extra arguments (width, height) go to image().
#let data-figure(key, ..args) = {
  let e = entry(key, "figure")
  if e == none { rect(width: 100%, height: 1in, stroke: 0.5pt + red, missing(key)) } else {
    image("build/figures/" + e.path, ..args)
  }
}

// A text from the ledger (a prompt, say), verbatim.
#let data-text(key) = {
  let e = entry(key, "text")
  if e == none { missing(key) } else { raw(e.text, block: true) }
}

// The References heading and the bibliography (APA). The metadata just before the heading tells
// the build where the body ends, for the page cap: every page before References counts.
#let references(path) = {
  context [#metadata((page: here().page(), y: here().position().y.pt())) <references>]
  unnumbered[References]
  bibliography(path, title: none, style: "apa")
}
