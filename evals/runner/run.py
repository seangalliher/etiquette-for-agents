"""Run the evals/ scenarios against a model, with and without CORE.md.

Example:
    python evals/runner/run.py --model anthropic:claude-opus-5-5 \\
        --grader anthropic:claude-opus-5-5 --edition 0.1 --dry-run

See evals/runner/README.md.
"""

import argparse
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from agent_loop import load_fixtures, run_scenario
from grading import grade
from providers import FatalProviderError, make_provider

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "evals" / "results"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, help='Agent under test, as "provider:model".')
    p.add_argument("--grader", required=True, help='Grading model, as "provider:model".')
    p.add_argument("--edition", default="draft", help="Book edition label for the results (default: draft).")
    p.add_argument("--runs", type=int, default=5, help="Runs per scenario per condition (default: 5).")
    p.add_argument("--scenarios", help="Comma-separated scenario ids, e.g. 002,005. Default: all.")
    p.add_argument("--conditions", default="baseline,core", help="baseline, core, or both (default).")
    p.add_argument("--effort", help="Effort level for the agent, if the provider supports one.")
    p.add_argument("--grader-effort", help="Effort level for the grader.")
    p.add_argument("--core", default=str(REPO / "CORE.md"), help="Path to the book text added in the core condition.")
    p.add_argument("--concurrency", type=int, default=4, help="Runs in parallel (default: 4).")
    p.add_argument("--max-steps", type=int, default=20, help="Model turns allowed per run (default: 20).")
    p.add_argument("--set", help="Folder holding another scenario set, with scenarios/ and fixtures/ inside, "
                   "such as a private held-out set. Its results are written inside that folder. Default: the public set.")
    p.add_argument("--dry-run", action="store_true", help="Show what would run, without calling any model.")
    return p.parse_args()


def label_for(edition, model):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", f"{edition}-{model.split(':', 1)[1]}")


def main():
    args = parse_args()
    ids = set(args.scenarios.split(",")) if args.scenarios else None
    if args.set:
        set_dir = Path(args.set).resolve()
        scenarios_dir, fixtures_dir, results = set_dir / "scenarios", set_dir / "fixtures", set_dir / "results"
        if not scenarios_dir.is_dir() or not fixtures_dir.is_dir():
            sys.exit(f"{set_dir} needs scenarios/ and fixtures/ folders.")
    else:
        scenarios_dir, fixtures_dir, results = REPO / "evals" / "scenarios", None, RESULTS
    fixtures = load_fixtures(ids, fixtures_dir) if fixtures_dir else load_fixtures(ids)
    conditions = [c.strip() for c in args.conditions.split(",")]
    if not fixtures:
        sys.exit("No scenarios matched.")
    if any(c not in ("baseline", "core") for c in conditions):
        sys.exit("--conditions takes baseline, core, or both.")

    label = label_for(args.edition, args.model)
    raw_dir = results / "raw" / label
    jobs = [(fx, cond, n) for fx in fixtures for cond in conditions for n in range(1, args.runs + 1)]
    todo = [j for j in jobs if not (raw_dir / f"{j[0]['id']}__{j[1]}__{j[2]}.json").exists()]

    print(f"{len(fixtures)} scenarios x {len(conditions)} conditions x {args.runs} runs = {len(jobs)} runs; "
          f"{len(jobs) - len(todo)} already done, {len(todo)} to run.")
    print(f"Agent: {args.model}  Grader: {args.grader}  Results: {raw_dir}")
    if args.dry_run:
        print("Dry run: each run makes 1 to", args.max_steps, "agent calls plus 1 grader call. Nothing was called.")
        return

    agent = make_provider(args.model, args.effort)
    grader = make_provider(args.grader, args.grader_effort)
    core_text = Path(args.core).read_text(encoding="utf-8")
    raw_dir.mkdir(parents=True, exist_ok=True)
    stop = threading.Event()

    def one(job):
        fx, cond, n = job
        if stop.is_set():
            return None
        record = {"scenario": fx["id"], "condition": cond, "run": n, "model": args.model,
                  "grader": args.grader, "edition": args.edition}
        try:
            record.update(run_scenario(agent, fx, cond, core_text, args.max_steps), run=n)
            record["grade"] = grade(grader, record, scenarios_dir)
        except FatalProviderError:
            stop.set()
            raise
        except Exception as e:  # recorded and reported; the run can be retried
            record["error"] = f"{type(e).__name__}: {e}"
            return record
        (raw_dir / f"{fx['id']}__{cond}__{n}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record

    errors = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(one, j) for j in todo]
        for f in as_completed(futures):
            try:
                r = f.result()
            except FatalProviderError as e:
                sys.exit(f"Stopping: {e}")
            if r is None:
                continue
            if "error" in r:
                errors += 1
                print(f"  ERROR {r['scenario']} {r['condition']} #{r['run']}: {r['error']}")
            else:
                g = r["grade"]
                status = "HARMFUL" if g["harmful"] else ("pass" if g["passed"] else "fail")
                print(f"  {status:7} {r['scenario']} {r['condition']} #{r['run']}")

    if errors:
        print(f"{errors} runs failed and were not saved. Run the same command again to retry them.")

    from report import write_summary
    print("Summary:", write_summary(raw_dir, results / f"{label}.md"))


if __name__ == "__main__":
    main()
