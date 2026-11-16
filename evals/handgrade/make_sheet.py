"""Build the public grading page: grade ten runs yourself and compare with the model grader.

    python evals/handgrade/make_sheet.py

Writes site/grade.html (published at bookforagents.com/grade.html) and evals/handgrade/sample.json.

The runs come from edition 0.1's final revision on the public scenarios. The sample is fixed, so
everyone grades the same runs and their grades can be compared: 4 runs the grader called harmful
(2 decided by a harmful tool call, 2 by the grader's own judgment), 3 it failed and 3 it passed,
half without the book and half with it, ten different scenarios, at most two runs per model.

The two runs decided by a tool call double as a check on attention: on an item the grader marked
harmful there, a careful reader marks "harmful" or "not met", not "met".
"""
import html
import json
import random
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evals/results/raw"
SCEN = ROOT / "evals/scenarios"
OUT = Path(__file__).parent
MODELS = "claude-sonnet-5.5 claude-haiku-5.5 gpt-6.1-sol gpt-6.1-terra gpt-4o-mini gemini-4-argon gemini-3.8-flash grok-4.7".split()


def outcome(g):
    return "harmful" if g["harmful"] else ("pass" if g["passed"] else "fail")


def kind(r):
    o = outcome(r["grade"])
    if o != "harmful":
        return o
    if r["harmful_tool_calls"]:
        # Usable as an attention check only if the grader also marked an item harmful.
        return "harm_tool" if any(i["verdict"] == "harmful" for i in r["grade"]["items"]) else None
    return "harm_judged"


runs = []
for m in MODELS:
    for p in sorted((RAW / f"0.1r4-{m}").glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        if "-" in r["scenario"]:  # variants need extra setup text; leave them out
            continue
        r["_path"] = str(p.relative_to(ROOT)).replace("\\", "/")
        r["_model"] = m
        r["_kind"] = kind(r)
        runs.append(r)

rng = random.Random(20261117)
rng.shuffle(runs)
plan = [("harm_tool", "baseline"), ("harm_tool", "core"), ("harm_judged", "baseline"), ("harm_judged", "core"),
        ("fail", "baseline"), ("fail", "core"), ("fail", "baseline"),
        ("pass", "core"), ("pass", "baseline"), ("pass", "core")]
picked, used_scen, model_count = [], set(), defaultdict(int)
for want, cond in plan:
    r = next(r for r in runs if r["_kind"] == want and r["condition"] == cond
             and r["scenario"] not in used_scen and model_count[r["_model"]] < 2)
    picked.append(r); used_scen.add(r["scenario"]); model_count[r["_model"]] += 1
rng.shuffle(picked)


def esc(s):
    return html.escape(s or "")


def shape(text):
    """A tool result with its numbers blanked, so 'Batch 4 migrated, 40 records' matches 'Batch 5 ...'."""
    return re.sub(r"\d+", "#", text.strip())


def odd_results(r):
    """Indexes of tool results that differ from the usual result of the same tool in this run.

    Only for tools called three or more times, where a long run of similar results can hide one that
    says something different. The rule looks only at the text's shape, not its meaning, so it marks a
    different result without saying whether it matters.
    """
    by_tool = defaultdict(list)
    for i, e in enumerate(r["events"]):
        if e["type"] == "tool":
            by_tool[e["name"]].append((i, shape(e["result"])))
    odd = set()
    for calls in by_tool.values():
        if len(calls) < 3:
            continue
        counts = defaultdict(int)
        for _, s in calls:
            counts[s] += 1
        usual, n = max(counts.items(), key=lambda kv: kv[1])
        if n >= 2:
            odd |= {i for i, s in calls if s != usual}
    return odd


def render_events(r):
    out = []
    odd = odd_results(r)
    for idx, e in enumerate(r["events"]):
        t = e["type"]
        if t == "history":
            out.append(f'<div class="msg hist"><b>Earlier, {esc(e["role"])}:</b><pre>{esc(e["text"])}</pre></div>')
        elif t == "user":
            out.append(f'<div class="msg user"><b>Person:</b><pre>{esc(e["text"])}</pre></div>')
        elif t == "assistant" and (e.get("text") or "").strip():
            out.append(f'<div class="msg agent"><b>Agent:</b><pre>{esc(e["text"])}</pre></div>')
        elif t == "tool":
            args = "\n".join(f"{k}: {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}" for k, v in e["args"].items())
            flag = ' <span class="harm">marked harmful in advance</span>' if e.get("harmful") else ""
            if idx in odd:
                out.append(f'<div class="msg tool odd"><b>Tool call:</b> <code>{esc(e["name"])}</code>{flag}'
                           f'<pre class="args">{esc(args)}</pre>'
                           f'<div class="res"><span class="oddtag">Different from the other {esc(e["name"])} results</span></div>'
                           f'<pre>{esc(e["result"])}</pre></div>')
            else:
                out.append(f'<div class="msg tool"><b>Tool call:</b> <code>{esc(e["name"])}</code>{flag}'
                           f'<pre class="args">{esc(args)}</pre><div class="res">Result:</div><pre>{esc(e["result"])}</pre></div>')
    return "\n".join(out)


def scenario(sid):
    f = next(SCEN.glob(f"{sid}-*.md"))
    text = f.read_text(encoding="utf-8")
    title = re.match(r"#\s*(.+)", text).group(1).strip()
    body = text.split("## Setup", 1)[1].split("## Good conduct")[0]
    body = re.sub(r"^## ", "", body, flags=re.M)
    return title, f.name, "Setup\n" + re.sub(r"\n{3,}", "\n\n", body).strip()


def model_name(m):
    return {"claude-sonnet-5.5": "Claude Sonnet 5.5", "claude-haiku-5.5": "Claude Haiku 5.5", "gpt-6.1-sol": "GPT-6.1 Sol",
            "gpt-6.1-terra": "GPT-6.1 Terra", "gpt-4o-mini": "GPT-4o mini", "gemini-4-argon": "Gemini 4 Argon",
            "gemini-3.8-flash": "Gemini 3.8 Flash", "grok-4.7": "Grok 4.7"}[m]


data = []
for i, r in enumerate(picked, 1):
    title, fname, setup = scenario(r["scenario"])
    items = r["grade"]["items"]
    data.append({
        "n": i, "path": r["_path"], "scenario": r["scenario"], "scenario_file": fname, "title": title,
        "model": model_name(r["_model"]), "condition": r["condition"], "tool_harm": bool(r["harmful_tool_calls"]),
        "check": [j for j, it in enumerate(items) if r["_kind"] == "harm_tool" and it["verdict"] == "harmful"],
        "items": [it["item"] for it in items],
        "grader": {"name": r["grader"].split(":")[-1], "verdicts": [it["verdict"] for it in items],
                   "reasons": [it["reason"] for it in items], "outcome": outcome(r["grade"])},
        "setup": setup, "transcript": render_events(r),
    })

(OUT / "sample.json").write_text(json.dumps(
    [{k: d[k] for k in ("n", "path", "scenario", "model", "condition")} | {"grader_outcome": d["grader"]["outcome"]} for d in data],
    indent=1), encoding="utf-8")
page = (OUT / "template.html").read_text(encoding="utf-8")
payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
(ROOT / "site/grade.html").write_text(page.replace("/*DATA*/[]", payload), encoding="utf-8")
print("runs:", [(d["scenario"], d["grader"]["outcome"], d["condition"], d["model"]) for d in data])
print("check runs:", [d["n"] for d in data if d["check"]])
