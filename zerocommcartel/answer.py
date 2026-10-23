"""Reading the answer line off a reply.

Copied verbatim from pilot/probe.py at 71d8b22 (pre-sprint code); later commits show the changes."""

import re

_NUM_RE = r"\$?\s*([0-9][0-9,]*(?:\.[0-9]+)?)"


ANSWER_KEY = {"cournot": "QUANTITY", "bertrand": "PRICE", "kyleq": "SHARES", "kylel": "LIMIT"}


def parse_number(game: str, reply: str):
    """The last 'QUANTITY: x' (PRICE, SHARES, LIMIT) in the reply, tolerating markdown bold and a $ sign. None if absent."""
    key = ANSWER_KEY[game]
    hits = re.findall(rf"{key}\s*\**\s*:\s*\**\s*{_NUM_RE}", reply, flags=re.I)
    if not hits:
        return None
    return float(hits[-1].replace(",", ""))
