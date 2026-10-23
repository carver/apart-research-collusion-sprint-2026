"""Reading the answer line off a reply.

The number pattern began as the pilot's (pilot/probe.py at 71d8b22); unlike it, it reads fractions."""

import re
from dataclasses import dataclass

_NUMBER = r"[0-9][0-9,]*(?:\.[0-9]+)?"
_NUM_RE = rf"\$?\s*({_NUMBER})(?:[ \t]*/[ \t]*({_NUMBER}))?"  # a fraction stays on its line
_SEP = r"\s*\**\s*:\s*\**\s*"  # "KEY:", tolerating markdown bold around either side of the colon


@dataclass(frozen=True)
class Answer:
    key: str | None  # the key of the reply's last answer line; None when it has none
    value: float | None  # the number, on a number line
    text: str | None  # the rest of the line, on a text line (an outlet's "DECLINE: <reason>")


def _number(numerator: str, denominator: str | None) -> float:
    """The number, or a fraction's quotient ("100/3"); a zero denominator is left out. Any a/b reads as its
    quotient, so a ratio such as 50/50 reads as 1."""
    value = float(numerator.replace(",", ""))
    divisor = float(denominator.replace(",", "")) if denominator else 0.0
    return value / divisor if divisor else value


def parse(reply: str, number_key: str, text_keys: tuple[str, ...] = ()) -> Answer:
    """The reply's last answer line: `number_key` followed by a number (a $ sign, commas and a fraction such
    as 100/3 allowed), or one of `text_keys`, at the start of a line, followed by any text. Keys match in any
    case."""
    hits = [
        (m.start(), Answer(number_key, _number(m[1], m[2]), None))
        for m in re.finditer(rf"{number_key}{_SEP}{_NUM_RE}", reply, flags=re.I)
    ]
    for key in text_keys:
        hits += [
            (m.start(), Answer(key, None, m[1].strip()))
            for m in re.finditer(rf"^[\s*_>]*{key}{_SEP}(\S.*)", reply, flags=re.I | re.M)
        ]
    return max(hits, key=lambda hit: hit[0])[1] if hits else Answer(None, None, None)
