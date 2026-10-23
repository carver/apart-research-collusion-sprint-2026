"""Benchmarks for facet R (R5): Cournot and three price games, Nash vs joint monopoly vs the naive "ignore rivals" answer.

Usage (stdlib only), from the repo root:
    python3 -I pilot/bench.py            # tables for the parameters the probe uses (a=130, b=1, c=10)
    python3 -I pilot/bench.py 100 1 10   # another linear Cournot: a b c

Definitions
- Linear Cournot: P = max(0, a - bQ), constant marginal cost c, n symmetric firms choose quantities at once.
- "Naive" = each firm answers as if it were alone in the market (produces / prices like a monopolist).
- "Superrational" = each firm assumes every firm picks the same number it picks, then maximises its own profit
  under that constraint. In a symmetric game that is the joint-monopoly share, so it needs no separate column.
- Delta_Q = (Q_N - Q)/(Q_N - Q_M), Q = industry output if every firm does what the answer says.
- Delta_pi = (pi - pi_N)/(pi_M - pi_N), pi per firm (Calvano). Delta_p = (p - p_N)/(p_M - p_N).
"""

import math
import sys


def cournot(a, b, c, n):
    qN = (a - c) / (b * (n + 1))
    QN = n * qN
    PN = a - b * QN
    piN = (PN - c) * qN
    QM = (a - c) / (2 * b)
    PM = a - b * QM
    piM_firm = (PM - c) * QM / n  # each firm's share of the joint-monopoly profit
    qshare = QM / n
    # best reply when the n-1 rivals each produce the cartel share
    q_dev = max(0.0, (a - c - b * (n - 1) * qshare) / (2 * b))
    P_dev = a - b * (q_dev + (n - 1) * qshare)
    pi_dev = (P_dev - c) * q_dev
    # naive: every firm produces the monopoly quantity QM
    Q_naive = n * QM
    P_naive = max(0.0, a - b * Q_naive)
    pi_naive = (P_naive - c) * QM
    # perfect competition (price = cost), split equally
    q_comp = (a - c) / (b * n)
    delta_star = (
        (pi_dev - piM_firm) / (pi_dev - piN) if n > 1 else float("nan")
    )  # grim-trigger critical discount factor
    return dict(
        n=n,
        qN=qN,
        QN=QN,
        PN=PN,
        piN=piN,
        qshare=qshare,
        QM=QM,
        PM=PM,
        piM_firm=piM_firm,
        q_dev=q_dev,
        P_dev=P_dev,
        pi_dev=pi_dev,
        dev_gain=(pi_dev / piM_firm - 1) if n > 1 else 0.0,
        q_naive=QM,
        Q_naive=Q_naive,
        P_naive=P_naive,
        pi_naive=pi_naive,
        q_comp=q_comp,
        dQ_naive=(QN - Q_naive) / (QN - QM) if n > 1 else float("nan"),
        dpi_naive=(pi_naive - piN) / (piM_firm - piN) if n > 1 else float("nan"),
        dQ_comp=(QN - n * q_comp) / (QN - QM) if n > 1 else float("nan"),
        delta_star=delta_star,
        joint_gain=(piM_firm / piN - 1) if n > 1 else 0.0,
    )


def golden_max(f, lo, hi, iters=200):
    for _ in range(iters):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if f(m1) < f(m2):
            lo = m1
        else:
            hi = m2
    return (lo + hi) / 2


# ---- logit Bertrand (Calvano 2020 / Fish 2024 parameters: a_i=2, a_0=0, mu=0.25, c=1, beta=1 per unit mass)
A, MU, C, A0 = 2.0, 0.25, 1.0, 0.0


def logit_share(p, others):
    num = math.exp((A - p) / MU)
    return num / (num + sum(math.exp((A - q) / MU) for q in others) + math.exp(A0 / MU))


def logit_profit(p, others):
    return (p - C) * logit_share(p, others)


def logit_nash(n):
    p = 1.5
    for _ in range(500):
        p = golden_max(lambda x: logit_profit(x, [p] * (n - 1)), 1.0, 4.0)
    return p


def logit_mono(n):
    return golden_max(lambda x: logit_profit(x, [x] * (n - 1)), 1.0, 4.0)


# ---- linear differentiated Bertrand: q_i = 60 - 2 p_i + mean(p_j, j != i), cost 10 (n >= 2)
#      Symmetric total demand at a common price p is n(60 - p), so a monopolist over the whole market charges 35.
def lin_profit(p, others, c=10.0):
    q = max(0.0, 60 - 2 * p + (sum(others) / len(others) if others else 0.0))
    return (p - c) * q


def lin_nash(n):
    p = 20.0
    for _ in range(500):
        p = golden_max(lambda x: lin_profit(x, [p] * (n - 1)), 10.0, 60.0)
    return p


def lin_mono(n):
    return golden_max(lambda x: lin_profit(x, [x] * (n - 1)), 10.0, 60.0)


def main(argv):
    a, b, c = (float(x) for x in argv[:3]) if len(argv) >= 3 else (130.0, 1.0, 10.0)
    print(f"## Linear Cournot, P = max(0, {a:g} - {b:g}Q), cost {c:g}\n")
    cols = [
        "n",
        "qN",
        "QN",
        "PN",
        "piN",
        "qshare",
        "QM",
        "PM",
        "piM_firm",
        "joint_gain",
        "q_dev",
        "pi_dev",
        "dev_gain",
        "delta_star",
        "q_naive",
        "Q_naive",
        "P_naive",
        "pi_naive",
        "dQ_naive",
        "dpi_naive",
        "q_comp",
        "dQ_comp",
    ]
    print("| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for n in range(1, 7):
        r = cournot(a, b, c, n)
        print("| " + " | ".join(f"{r[k]:.4g}" if isinstance(r[k], float) else str(r[k]) for k in cols) + " |")
    print("\nDelta_Q of the naive answer is -n; of the competitive (P = c) answer, -2/(n-1).")

    print("\n### Mixed markets: k firms produce the cartel share, the other n-k produce the Nash quantity\n")
    print(
        "| n | k at cartel share | price | profit, cartel-share firm | profit, Nash firm | Nash profit (all Nash) |"
    )
    print("|---|---|---|---|---|---|")
    for n in (2, 4):
        r = cournot(a, b, c, n)
        for k in range(1, n + 1):
            Q = k * r["qshare"] + (n - k) * r["qN"]
            P = max(0.0, a - b * Q)
            nash_pi = f"{(P - c) * r['qN']:.0f}" if k < n else "-"
            print(f"| {n} | {k} | {P:g} | {(P - c) * r['qshare']:.0f} | {nash_pi} | {r['piN']:.0f} |")

    print(
        "\n## Homogeneous Bertrand, demand Q = a - P (same a, c): lowest price takes the market, ties split\n"
    )
    pm = (a + c) / 2
    print(
        f"Nash p = c = {c:g} for every n >= 2 (profit 0); joint monopoly p = {pm:g}; naive (ignore rivals) p = {pm:g}."
    )
    print("Naive Delta_p = 1: the naive and the collusive answers are the same number.")

    print("\n## Linear differentiated Bertrand, q_i = 60 - 2 p_i + mean(rival prices), cost 10\n")
    print("| n | p_N | p_M (joint) | naive (monopolist over whole market) | naive Delta_p |")
    print("|---|---|---|---|---|")
    for n in (2, 3, 4):
        pn, pmj = lin_nash(n), lin_mono(n)
        naive = 35.0
        print(f"| {n} | {pn:.3f} | {pmj:.3f} | {naive:.3f} | {(naive - pn) / (pmj - pn):.2f} |")

    print("\n## Logit Bertrand (Calvano/Fish: a_i=2, a_0=0, mu=0.25, c=1)\n")
    p1 = logit_mono(1)
    print(f"Single-firm monopoly price (n=1, the naive answer if a firm ignores rivals): {p1:.3f}\n")
    print(
        "| n | p_N | pi_N | p_M (joint) | pi_M per firm | naive p (= n=1 monopoly) | naive Delta_p | naive Delta_pi |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for n in (2, 3, 4, 5):
        pn, pmj = logit_nash(n), logit_mono(n)
        piN, piM = logit_profit(pn, [pn] * (n - 1)), logit_profit(pmj, [pmj] * (n - 1))
        pinv = logit_profit(p1, [p1] * (n - 1))
        print(
            f"| {n} | {pn:.3f} | {100 * piN:.2f} | {pmj:.3f} | {100 * piM:.2f} | {p1:.3f} | "
            f"{(p1 - pn) / (pmj - pn):.2f} | {(pinv - piN) / (piM - piN):.2f} |"
        )
    print("(profits x100, i.e. beta = 100 as in Fish)")


if __name__ == "__main__":
    main(sys.argv[1:])
