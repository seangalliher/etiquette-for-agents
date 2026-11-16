"""Render one raw result file as a readable Markdown transcript.

Example:
    python evals/runner/transcript.py evals/results/raw/0.1r4-gpt-6.1-sol/007__core__1.json > out.md

Shows the conversation, every tool call and its result (harmful calls are marked), the agent's
final message, and the grader's verdict on each item. The agent's role prompt and, in the core
condition, CORE.md are not repeated; they are in the scenario's fixture and in CORE.md.
"""

import json
import sys
from pathlib import Path

VERDICT = {"met": "✅ met", "not_met": "❌ not met", "harmful": "⛔ harmful", "not_applicable": "– not applicable"}


def quote(text):
    return "\n".join("> " + line if line else ">" for line in text.strip().splitlines())


def render(record):
    cond = "with CORE.md" if record["condition"] == "core" else "without the book"
    g = record["grade"]
    outcome = "harmful" if g["harmful"] else ("passed" if g["passed"] else "failed")
    model = record["model"].split(":", 1)[-1]
    grader = record.get("grader", "").split(":", 1)[-1]
    out = [f"# Scenario {record['scenario']}, {model}, {cond} (run {record['run']})", "",
           f"**Outcome: {outcome}.** Graded by {grader}. Edition {record['edition']}.", ""]
    for e in record["events"]:
        t = e["type"]
        if t == "history":
            out += [f"**Earlier, {e['role']}:**", "", quote(e["text"]), ""]
        elif t == "user":
            out += ["**Person:**", "", quote(e["text"]), ""]
        elif t == "assistant":
            if e.get("text", "").strip():
                out += ["**Agent:**", "", quote(e["text"]), ""]
        elif t == "tool":
            args = ", ".join(f"{k}={json.dumps(v)}" for k, v in e["args"].items())
            mark = " ⛔ **marked harmful**" if e.get("harmful") else ""
            out += [f"**Tool call:** `{e['name']}({args})`{mark}", "", "```", e["result"].strip(), "```", ""]
    out += ["## Grade", ""]
    for it in g["items"]:
        out += [f"- {VERDICT.get(it['verdict'], it['verdict'])}: {it['item']}", f"  - {it['reason']}"]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(render(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))), end="")
