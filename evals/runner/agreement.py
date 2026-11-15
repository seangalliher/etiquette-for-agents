"""Re-grade a sample of recorded runs with a second grader and report how often the graders agree.

Example:
    python agreement.py --raw ../results/raw/0.1r2-gpt-4o-mini --grader openai:gemini-4-argon --fraction 0.1

The second grade is stored in each sampled record under "second_grade"; the primary
grade is not changed. Running again reuses second grades already recorded by the same
grader, so an interrupted check can be resumed.
"""

import argparse
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from agent_loop import load_fixtures
from grading import SCENARIOS, grade
from providers import make_provider


def kappa(pairs):
    """Cohen's kappa for a list of (a, b) labels."""
    n = len(pairs)
    if not n:
        return float("nan")
    labels = {x for p in pairs for x in p}
    observed = sum(a == b for a, b in pairs) / n
    expected = sum((sum(a == l for a, _ in pairs) / n) * (sum(b == l for _, b in pairs) / n) for l in labels)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def outcome(g):
    return "harmful" if g["harmful"] else ("pass" if g["passed"] else "fail")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raw", nargs="+", required=True, help="Raw result folders to sample from.")
    p.add_argument("--grader", required=True, help='Second grader, as "provider:model".')
    p.add_argument("--set", help="Scenario set folder (with scenarios/ and fixtures/), if not the public set.")
    p.add_argument("--fraction", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--concurrency", type=int, default=4)
    args = p.parse_args()

    if args.set:
        scenarios_dir = Path(args.set) / "scenarios"
        fixtures = {f["id"]: f for f in load_fixtures(None, Path(args.set) / "fixtures")}
    else:
        scenarios_dir = SCENARIOS
        fixtures = {f["id"]: f for f in load_fixtures()}

    paths = sorted(p for d in args.raw for p in Path(d).glob("*.json"))
    rng = random.Random(args.seed)
    sample = rng.sample(paths, max(1, round(len(paths) * args.fraction)))
    grader = make_provider(args.grader, None)

    def one(path):
        record = json.loads(path.read_text(encoding="utf-8"))
        prior = record.get("second_grade")
        if prior and prior.get("grader") == args.grader:
            return record
        g = grade(grader, record, scenarios_dir, fixtures[record["scenario"]])
        g["grader"] = args.grader
        record["second_grade"] = g
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record

    records, errors = [], 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for f in as_completed([pool.submit(one, p) for p in sample]):
            try:
                records.append(f.result())
            except Exception as e:
                errors += 1
                print("  ERROR", type(e).__name__, str(e)[:200])

    runs = [(outcome(r["grade"]), outcome(r["second_grade"])) for r in records]
    items = [(a["verdict"], b["verdict"])
             for r in records for a, b in zip(r["grade"]["items"], r["second_grade"]["items"])]
    agree = sum(a == b for a, b in runs)
    print(f"Sampled {len(sample)} runs; graded {len(records)}; errors {errors}.")
    print(f"Run outcome (pass/fail/harmful): agree {agree}/{len(runs)} ({agree / max(1, len(runs)):.0%}), kappa {kappa(runs):.2f}")
    print(f"Item verdicts: agree {sum(a == b for a, b in items)}/{len(items)}, kappa {kappa(items):.2f}")
    flips = {}
    for a, b in runs:
        if a != b:
            flips[(a, b)] = flips.get((a, b), 0) + 1
    for (a, b), n in sorted(flips.items()):
        print(f"  primary {a} -> second {b}: {n}")


if __name__ == "__main__":
    main()
