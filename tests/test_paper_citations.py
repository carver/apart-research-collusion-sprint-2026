"""The build's citation check: a source the paper cites must have a row in citations.md saying someone read it
in full; a source it doesn't cite, or a label that isn't a citation, isn't checked."""

from paper.checks import Problem, unread_citations

BIB = """@article{read2020,
  title = {Read},
}

@book{skimmed2019,
  title = {Skimmed},
}

@misc{rowless2024,
  title = {No row},
}

@misc{uncited2021,
  title = {Uncited},
}

  @misc{ spaced2022 ,
  title = {Indented, with spaces round its key},
}
"""

TABLE = """# Citations

| key | source | read | used for | where | in the paper |
|---|---|---|---|---|---|
| `read2020` | A (2020) | full text | a fact | intro | yes |
| `skimmed2019` | B (2019) | catalogue | a fact | intro | yes |
| `uncited2021` | C (2021) | not checked | a fact | nowhere | no |

Read only by title, so not cited: D (1999).
"""


def test_a_cited_source_read_in_full_passes():
    assert unread_citations({"read2020", "fig-game"}, BIB, TABLE) == []


def test_a_cited_source_not_read_in_full_is_a_problem_saying_how_much_was_read():
    assert unread_citations({"read2020", "skimmed2019"}, BIB, TABLE) == [
        Problem("citation", "@skimmed2019 is cited, but citations.md says only its catalogue was read"),
    ]


def test_a_cited_source_with_no_row_is_a_problem():
    assert unread_citations({"rowless2024"}, BIB, TABLE) == [
        Problem("citation", "@rowless2024 is cited, but citations.md has no row for it"),
    ]


def test_an_entry_indented_or_spaced_round_its_key_is_still_a_bibliography_key():
    assert unread_citations({"spaced2022"}, BIB, TABLE) == [
        Problem("citation", "@spaced2022 is cited, but citations.md has no row for it"),
    ]


def test_an_uncited_source_and_a_label_that_isnt_a_citation_go_unchecked():
    assert unread_citations({"fig-game", "app-pilot"}, BIB, TABLE) == []
    assert unread_citations(set(), BIB, TABLE) == []
