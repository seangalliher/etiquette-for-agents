"""Builds the results summary from saved run records."""

import json
import sys
from collections import defaultdict
from pathlib import Path


def _sort_key(scenario_id):
    base, _, variant = scenario_id.partition("-")
    prefix = base.rstrip("0123456789")
    return (prefix, int(base[len(prefix):] or 0), variant)


def write_summary(raw_dir, out_path):
    raw_dir, out_path = Path(raw_dir), Path(out_path)
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(raw_dir.glob("*.json"))]
    if not records:
        raise SystemExit(f"No run records in {raw_dir}")

    cells = defaultdict(lambda: {"runs": 0, "passed": 0, "harmful": 0, "refused": 0})
    tokens = defaultdict(int)
    for r in records:
        c = cells[(r["scenario"], r["condition"])]
        c["runs"] += 1
        c["passed"] += r["grade"]["passed"]
        c["harmful"] += r["grade"]["harmful"]
        c["refused"] += r["outcome"] == "refused"
        for k, v in r["usage"].items():
            tokens[(r["condition"], k)] += v
        for k, v in r["grade"].get("usage", {}).items():
            tokens[("grader", k)] += v

    first = records[0]
    scenarios = sorted({s for s, _ in cells}, key=_sort_key)
    lines = [
        f"# Edition {first['edition']}, {first['model'].split(':', 1)[1]}",
        "",
        f"**Agent:** `{first['model']}`  ",
        f"**Grader:** `{first['grader']}` (model-graded; check a sample by hand)  ",
        f"**Runs per condition:** up to {max(c['runs'] for c in cells.values())}  ",
        "**Setup notes:** simulated tools from `evals/runner/fixtures/`; CORE.md appended to the system prompt in the core condition.",
        "",
        "| # | Without book: pass | Without book: harmful | With CORE.md: pass | With CORE.md: harmful |",
        "|---|---|---|---|---|",
    ]
    totals = {cond: {"runs": 0, "passed": 0, "harmful": 0} for cond in ("baseline", "core")}
    for s in scenarios:
        row = [s]
        for cond in ("baseline", "core"):
            c = cells.get((s, cond))
            if c is None:
                row += ["-", "-"]
                continue
            row += [f"{c['passed']}/{c['runs']}", str(c["harmful"])]
            for k in totals[cond]:
                totals[cond][k] += c[k]
        lines.append("| " + " | ".join(row) + " |")
    b, k = totals["baseline"], totals["core"]
    lines.append(f"| **All** | {b['passed']}/{b['runs']} | {b['harmful']} | {k['passed']}/{k['runs']} | {k['harmful']} |")

    refusals = sum(c["refused"] for c in cells.values())
    lines += [
        "",
        "## Observations",
        "",
        "*To be written after reading the transcripts.*",
        "",
        "## Run details",
        "",
        f"- Model refusals: {refusals}",
    ]
    for cond in ("baseline", "core"):
        if tokens[(cond, "input_tokens")]:
            lines.append(f"- Agent tokens, {cond}: {tokens[(cond, 'input_tokens')]:,} input, "
                         f"{tokens[(cond, 'output_tokens')]:,} output")
    if tokens[("grader", "input_tokens")]:
        lines.append(f"- Grader tokens, all runs: {tokens[('grader', 'input_tokens')]:,} input, "
                     f"{tokens[('grader', 'output_tokens')]:,} output")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python evals/runner/report.py <raw-dir> <summary.md>")
    print(write_summary(sys.argv[1], sys.argv[2]))
