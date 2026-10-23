"""Table helpers.

Copied verbatim from pilot/analyze.py at 71d8b22 (pre-sprint code); later commits show the changes."""

import statistics


def quartiles(xs):
    if len(xs) < 2:
        return (xs[0], xs[0]) if xs else (None, None)
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return q[0], q[2]


def fmt(x, d=1):
    return "-" if x is None else (f"{x:.{d}f}".rstrip("0").rstrip(".") if isinstance(x, float) else str(x))
