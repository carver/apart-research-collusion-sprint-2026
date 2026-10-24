"""The sprint's rules for the report (requirements.md), checked on a typeset paper, and the extra checks of a
final build: every link resolves, and the paper and its logs are committed and pushed."""

import http.client
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from paper.git import Repo
from paper.typeset import Typeset

PAGE_CAP = 8  # pages before References
ABSTRACT_WORDS = (150, 250)
MAX_BYTES = 25_000_000  # the submission form's limit
LIMITATIONS = "Limitations and Dual-Use / Ethical Considerations"  # the appendix the rules require
REQUIRED_SECTIONS = ("Code and Data", "LLM Usage Statement", LIMITATIONS)
DOI = ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/")
TOP = 73.0  # pt: the top margin, so a References heading at or above this height starts its page
USER_AGENT = "Mozilla/5.0 (paper link check; zerocommcartel)"


@dataclass(frozen=True)
class Problem:
    check: str
    detail: str


def body_pages(page: Typeset) -> int | None:
    """Pages before References: its page counts unless the heading starts it."""
    if page.references is None:
        return None
    number, y = page.references
    return number - 1 if y <= TOP else number


def failed_claims(page: Typeset) -> list[str]:
    return [
        text if ok is False else f"{text} (can't be checked: a key isn't in the ledger)"
        for ok, text in page.claims
        if ok is not True
    ]


def unreferenced(page: Typeset) -> list[str]:
    return [figure for figure in page.figures if figure not in page.refs]


def missing_sections(page: Typeset) -> list[str]:
    return [section for section in REQUIRED_SECTIONS if section not in page.headings]


def rules(page: Typeset) -> list[Problem]:
    """Every rule the paper breaks. A draft prints them; a final build refuses them."""
    problems = [Problem("typst", warning) for warning in page.warnings]
    problems += [Problem("missing", missing) for missing in page.missing]
    problems += [Problem("claim", claim) for claim in failed_claims(page)]
    if page.todos:
        problems.append(Problem("todo", f"{page.todos} TODO markers"))
    problems += [Problem("unreferenced", figure) for figure in unreferenced(page)]
    problems += [Problem("sections", f"no {section} section") for section in missing_sections(page)]
    headings = page.headings
    if {LIMITATIONS, "References"} <= set(headings) and headings.index(LIMITATIONS) < headings.index(
        "References"
    ):
        problems.append(Problem("sections", f"{LIMITATIONS} comes before References; it must be an appendix"))
    pages = body_pages(page)
    if pages is None:
        problems.append(Problem("page-cap", "no References heading, so the pages can't be counted"))
    elif pages > PAGE_CAP:
        problems.append(Problem("page-cap", f"{pages} pages before References (cap {PAGE_CAP})"))
    words, (low, high) = len(page.abstract.split()), ABSTRACT_WORDS
    if not low <= words <= high:
        problems.append(Problem("abstract", f"{words} words (needs {low}-{high})"))
    if len(page.pdf) > MAX_BYTES:
        problems.append(Problem("size", f"{len(page.pdf)} bytes (cap {MAX_BYTES})"))
    return problems


def probe_url(url: str) -> str:
    """The URL to request to learn whether `url` resolves. A DOI goes to doi.org's handle API, which answers
    404 for a DOI it doesn't know, rather than to the publisher, whose site often refuses scripts."""
    doi = next((url.removeprefix(prefix) for prefix in DOI if url.startswith(prefix)), None)
    return url if doi is None else f"https://doi.org/api/handles/{doi}"


def unreachable(url: str) -> str | None:
    """Why the URL doesn't resolve, or None when it does."""
    request = urllib.request.Request(probe_url(url), headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=20):
            return None
    except urllib.error.HTTPError as error:
        return f"HTTP {error.code}"
    except (ValueError, http.client.InvalidURL) as error:
        return f"invalid URL ({error})"
    except (urllib.error.URLError, OSError) as error:
        return f"unreachable ({getattr(error, 'reason', error)})"


def broken_links(page: Typeset) -> list[Problem]:
    """Every web link that doesn't resolve. A network failure counts: the link wasn't shown to work."""
    urls = sorted({link for link in page.links if link.startswith(("http://", "https://"))})
    with ThreadPoolExecutor(max_workers=8) as pool:
        reasons = pool.map(unreachable, urls)
    return [Problem("link", f"{url}: {why}") for url, why in zip(urls, reasons, strict=True) if why]


def unshipped(repo: Repo | None, logs: list[str]) -> list[Problem]:
    """What keeps the build from matching a commit anyone can check out: uncommitted changes, and logs the
    numbers came from that aren't committed or pushed to origin/main."""
    if repo is None:
        return [Problem("git", "the paper isn't in a git repository")]
    return [
        *(Problem("dirty", path) for path in repo.dirty()),
        *(Problem("unpushed", log) for log in repo.unpushed(logs)),
    ]
