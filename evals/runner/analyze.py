"""Compare models across result folders, with 95% confidence intervals.

Example:
    python analyze.py ../results/raw/0.1r2-* --out ../results/0.1r2-summary.md

Intervals come from a cluster bootstrap: scenarios are resampled with replacement, and
each resampled scenario brings all of its runs. This accounts for runs of the same
scenario being more alike than runs of different scenarios.
"""

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def load(raw_dir):
    """{scenario: {condition: [(passed, harmful), ...]}} for graded runs."""
    out = defaultdict(lambda: defaultdict(list))
    for path in Path(raw_dir).glob("*.json"):
        r = json.loads(path.read_text(encoding="utf-8"))
        if "grade" in r:
            out[r["scenario"]][r["condition"]].append((r["grade"]["passed"], r["grade"]["harmful"]))
    return out


def rate(data, scenarios, cond, idx):
    runs = [run[idx] for s in scenarios for run in data[s].get(cond, [])]
    return sum(runs) / len(runs) if runs else float("nan")


def bootstrap(data, stat, n=2000, seed=1):
    rng = random.Random(seed)
    scenarios = sorted(data)
    values = sorted(stat([rng.choice(scenarios) for _ in scenarios]) for _ in range(n))
    return values[int(0.025 * n)], values[int(0.975 * n) - 1]


def pct(x):
    return f"{100 * x:.0f}%"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("raw", nargs="+", help="Raw result folders, one per model.")
    p.add_argument("--out", help="Write the markdown table here as well as printing it.")
    args = p.parse_args()

    rows = ["| Model | Runs | Pass, without | Pass, with CORE | Change (95% CI) | Harmful, without | Harmful, with |",
            "|---|---|---|---|---|---|---|"]
    for raw in args.raw:
        data = load(raw)
        # Only scenarios that have both conditions, so the comparison is like for like.
        data = {s: c for s, c in data.items() if c.get("baseline") and c.get("core")}
        if not data:
            continue
        sc = sorted(data)
        n_runs = sum(len(data[s][c]) for s in sc for c in ("baseline", "core"))
        b, c = rate(data, sc, "baseline", 0), rate(data, sc, "core", 0)
        lo, hi = bootstrap(data, lambda s: rate(data, s, "core", 0) - rate(data, s, "baseline", 0))
        hb = sum(run[1] for s in sc for run in data[s]["baseline"])
        hc = sum(run[1] for s in sc for run in data[s]["core"])
        nb = sum(len(data[s]["baseline"]) for s in sc)
        nc = sum(len(data[s]["core"]) for s in sc)
        name = Path(raw).name
        rows.append(f"| {name} | {n_runs} | {pct(b)} | {pct(c)} | {100 * (c - b):+.0f} pts ({100 * lo:+.0f} to {100 * hi:+.0f}) "
                    f"| {hb}/{nb} | {hc}/{nc} |")
    table = "\n".join(rows)
    print(table)
    if args.out:
        Path(args.out).write_text(table + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
