// Clone of the official Apart Research sprint template (paper/template/apart-template.docx).
// Layout facts taken from the docx: US Letter, 1-inch margins, Old Standard TT throughout,
// body 11 pt at 1.15 line spacing, title 20 pt bold between a 3 pt and a 1 pt rule,
// section headings 14 pt bold #434343, subsection headings 13 pt bold #666666,
// abstract heading 14 pt bold centred, abstract body justified and inset (~0.99 in left,
// ~1.13 in right), footnotes 10 pt. Fonts: build.sh passes --font-path.

#let todo-color = rgb("#c00000")

// A result or decision still to come. Renders in red so no placeholder survives unseen;
// build.sh counts them.
#let TODO(body) = text(fill: todo-color, weight: "bold")[[TODO: #body]]

// A multi-line skeleton note (what a section will say once results land), in red.
#let todo-block(body) = block(
  stroke: (left: 1.5pt + todo-color), inset: (left: 6pt, y: 2pt), width: 100%,
  text(fill: todo-color, size: 10pt)[*TODO.* #body],
)

// A figure that doesn't exist yet: a grey box of the given height with its caption.
#let todo-figure(height: 2in, caption: [], body) = figure(
  rect(width: 100%, height: height, stroke: 0.5pt + todo-color, fill: luma(245),
    align(center + horizon, text(fill: todo-color, size: 10pt)[*TODO figure.* #body])),
  caption: caption,
)

#let heading-gray = rgb("#434343")
#let subheading-gray = rgb("#666666")
#let link-blue = rgb("#1155cc")

#let apart(
  title: "Project Title",
  authors: (),
  abstract: [],
  sprint-name: "AI Collusion Research Sprint",
  sprint-url: "https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25",
  sprint-date: "October 2026",
  body,
) = {
  set document(title: title)
  // The template PDF carries no page numbers; set numbering: "1" here to add them.
  set page(paper: "us-letter", margin: 1in)
  set text(font: "Old Standard TT", size: 11pt, lang: "en", top-edge: "ascender", bottom-edge: "descender")
  // Google Docs "1.15" on Old Standard TT gives ~15.5 pt from baseline to baseline at 11 pt.
  set par(leading: 0.41em, spacing: 0.8em, justify: false)
  show link: it => text(fill: link-blue, underline(it))

  set footnote.entry(separator: line(length: 2in, stroke: 0.5pt), gap: 0.4em)
  show footnote.entry: set text(size: 10pt)

  // Section headings: "1. Introduction", 14 pt bold, dark gray (docx Heading2 as used).
  set heading(numbering: (..n) => if n.pos().len() == 1 { numbering("1.", ..n) })
  show heading.where(level: 1): it => {
    set text(size: 14pt, weight: "bold", fill: heading-gray)
    set par(justify: false)
    block(above: 1.35em, below: 0.75em, sticky: true, {
      if it.numbering != none and it.outlined { counter(heading).display(it.numbering) + h(0.3em) }
      it.body
    })
  }
  // Subsections ("Limitations", "Future Work"): 13 pt bold, lighter gray, unnumbered.
  show heading.where(level: 2): it => {
    set text(size: 13pt, weight: "bold", fill: subheading-gray)
    block(above: 1.1em, below: 0.6em, sticky: true, it.body)
  }
  show heading.where(level: 3): it => {
    set text(size: 11pt, weight: "bold", fill: subheading-gray)
    block(above: 0.9em, below: 0.5em, sticky: true, it.body)
  }

  set figure(gap: 0.6em)
  show figure.caption: set text(size: 10pt)
  show figure.caption: set par(justify: true)
  show figure.caption: set align(left)
  show figure.where(kind: table): set figure.caption(position: top)
  set table(stroke: 0.5pt + luma(140), inset: (x: 4pt, y: 2.5pt))
  show table: set text(size: 9pt)
  show table: set par(justify: false, leading: 0.3em)

  set list(indent: 1em)
  set enum(indent: 1em)

  // ---- Title block ------------------------------------------------------------------
  v(0.25in)
  line(length: 100%, stroke: 3pt)
  v(14pt)
  align(center, text(size: 20pt, weight: "bold", hyphenate: false, {
    set par(leading: 0.2em)
    title
    footnote(numbering: "1")[#h(0.2em)Research conducted at the #link(sprint-url)[#sprint-name], #sprint-date]
  }))
  v(15pt)
  line(length: 100%, stroke: 1pt)
  v(21pt)

  // Author block: a centred grid of up to three authors per row (docx Table2, 5 in wide).
  // The author block and "With Apart Research" use single line spacing, as in the docx.
  let cols = calc.min(calc.max(authors.len(), 1), 3)
  {
    set par(leading: 0.22em)
    align(center, block(width: if cols == 1 { 2.6in } else { 5in }, grid(
      columns: (1fr,) * cols,
      row-gutter: 11pt,
      ..authors.map(a => align(center, [#a.name \ #a.affiliation])),
    )))
    v(6pt)
    align(center)[*With* \ Apart Research]
  }

  // Abstract.
  v(12pt)
  align(center, text(size: 14pt, weight: "bold")[Abstract])
  v(16pt)
  pad(left: 0.99in, right: 1.13in, par(justify: true, abstract))
  v(10pt)

  body
}

// Unnumbered section heading in the level-1 style (Code and Data, References, Appendix).
#let unnumbered(title) = heading(level: 1, numbering: none, outlined: false, title)

// Appendix sections lettered A, B, ...
#let appendix(body) = {
  counter(heading).update(0)
  set heading(numbering: (..n) => if n.pos().len() == 1 { numbering("A.", ..n) })
  body
}
