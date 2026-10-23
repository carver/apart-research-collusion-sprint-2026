"""Samples per cell needed to detect a shift from Delta ~ 0 to Delta ~ 0.5 between two arms of the one-shot probe.

Usage, from the repo root:
    uv run --with scipy python -I pilot/power.py

Two ways a cell can move from 0 to 0.5, since one-shot answers sit on focal points (Nash, cartel share):
  mixture: each answer is the cartel share with probability m and otherwise a draw from the control cell (m = 0.5
           gives mean Delta 0.5); outcome tested by Fisher's exact test on "at cartel" and by Mann-Whitney on Delta.
  shift:   every answer moves by +0.5 in Delta, with the control cell's spread (or a Normal spread of a given SD when
           the control cell has none); Mann-Whitney on Delta.
The control is every Cournot base-arm answer in probe-results.jsonl, pooled over models and n.
Alpha 0.05 two-sided, and 0.05/6 for six pre-registered contrasts (Bonferroni, a conservative stand-in for Holm).
"""

import json
import random
import sys
from pathlib import Path

from scipy.stats import fisher_exact, mannwhitneyu

RESULTS = Path(__file__).resolve().parent.parent / "logs" / "pilot" / "probe-results.jsonl"
RNG = random.Random(7)


def delta(n, q):
    qn = 120 / (n + 1)
    return (n * qn - n * q) / (n * qn - 60)


def control_cells(path):
    cells = {}
    for line in Path(path).read_text().splitlines():
        r = json.loads(line)
        if r["game"] == "cournot" and r["arm"] == "base" and r.get("value") is not None:
            cells.setdefault((r["model"], r["n"]), []).append(delta(r["n"], r["value"]))
    return cells


def power(control, k, scenario, m=0.5, sd=None, alpha=0.05, sims=2000):
    hits_f = hits_u = 0
    for _ in range(sims):
        a = [RNG.choice(control) for _ in range(k)]
        if scenario == "mixture":
            b = [1.0 if RNG.random() < m else RNG.choice(control) for _ in range(k)]
        else:
            b = [RNG.choice(control) + 0.5 + (RNG.gauss(0, sd) if sd else 0.0) for _ in range(k)]
            a = [x + (RNG.gauss(0, sd) if sd else 0.0) for x in a]
        ca, cb = sum(abs(x - 1) < 0.05 for x in a), sum(abs(x - 1) < 0.05 for x in b)
        if scenario == "mixture" and fisher_exact([[ca, k - ca], [cb, k - cb]])[1] < alpha:
            hits_f += 1
        if len(set(a + b)) > 1 and mannwhitneyu(a, b, alternative="two-sided")[1] < alpha:
            hits_u += 1
    return hits_f / sims, hits_u / sims


def main(argv):
    cells = control_cells(RESULTS)
    pooled = [d for v in cells.values() for d in v]
    sds = sorted(
        {
            round((sum((x - sum(v) / len(v)) ** 2 for x in v) / max(1, len(v) - 1)) ** 0.5, 3)
            for v in cells.values()
        }
    )
    print(
        f"control cells (Cournot base arm): {len(cells)}, answers {len(pooled)}, within-cell SDs of Delta: {sds}"
    )
    print(f"pooled control Delta values: {sorted(set(round(d, 3) for d in pooled))}\n")
    ks = [3, 5, 8, 10, 15, 20, 30]
    print("| scenario | alpha | test | " + " | ".join(f"k={k}" for k in ks) + " |")
    print("|---|---|---|" + "---|" * len(ks))
    for alpha in (0.05, 0.05 / 6):
        res = [power(pooled, k, "mixture", alpha=alpha) for k in ks]
        print(
            f"| mixture m=0.5 | {alpha:.3g} | Fisher at-cartel | "
            + " | ".join(f"{f:.2f}" for f, _ in res)
            + " |"
        )
        print(
            f"| mixture m=0.5 | {alpha:.3g} | Mann-Whitney | " + " | ".join(f"{u:.2f}" for _, u in res) + " |"
        )
        for sd in (0.25, 0.5, 1.0):
            res = [power(pooled, k, "shift", sd=sd, alpha=alpha, sims=1000) for k in ks]
            print(
                f"| shift +0.5, SD {sd} | {alpha:.3g} | Mann-Whitney | "
                + " | ".join(f"{u:.2f}" for _, u in res)
                + " |"
            )


if __name__ == "__main__":
    main(sys.argv[1:])
