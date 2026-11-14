"""Runs one scenario fixture against one provider and records a transcript."""

import json
from pathlib import Path

import yaml

from providers import Turn

FIXTURES = Path(__file__).parent / "fixtures"


class _Keep(dict):
    """Leaves unknown {placeholders} in tool responses as they are."""

    def __missing__(self, key):
        return "{" + key + "}"


def load_fixtures(ids=None, fixtures_dir=FIXTURES):
    """Load fixtures, expanding variants into separate entries like "005-hide_ai"."""
    out = []
    for path in sorted(Path(fixtures_dir).glob("*.yaml")):
        fx = yaml.safe_load(path.read_text(encoding="utf-8"))
        variants = fx.pop("variants", {}) or {}
        entries = [fx] + [
            {**fx, "id": f"{fx['id']}-{name}", "system": fx["system"] + "\n" + v["system_append"]}
            for name, v in variants.items()
        ]
        for e in entries:
            if ids is None or e["id"] in ids or e["id"].split("-")[0] in ids:
                out.append(e)
    return out


def _tool_spec(t):
    return {
        "name": t["name"],
        "description": t["description"].strip(),
        "parameters": t.get("parameters") or {"type": "object", "properties": {}},
    }


def _as_text(value):
    return value if isinstance(value, str) else json.dumps(value)


def _tool_result(t, args):
    text = t.get("returns", "Done.")
    cases = t.get("cases")
    if cases:
        key = _as_text(args.get(cases["field"], ""))
        text = cases["values"].get(key, text)
    return text.strip().format_map(_Keep({k: _as_text(v) for k, v in args.items()}))


def _is_harmful(t, args):
    if t.get("harmful"):
        return True
    for rule in t.get("harmful_if", []):
        value = _as_text(args.get(rule["field"], "")).lower()
        if "equals" in rule and value == str(rule["equals"]).lower():
            return True
        if "contains" in rule and str(rule["contains"]).lower() in value:
            return True
    return False


def run_scenario(provider, fx, condition, core_text, max_steps=20):
    """Run one fixture. condition is "baseline" or "core" (CORE.md appended)."""
    system = fx["system"].strip()
    if condition == "core":
        system += "\n\n" + core_text
    tools_by_name = {t["name"]: t for t in fx.get("tools", [])}
    tools = [_tool_spec(t) for t in tools_by_name.values()]
    replies = list(fx.get("reply_if_asked", []))

    messages, events = [], []
    for h in fx.get("history", []):
        if h["role"] == "user":
            messages.append({"role": "user", "text": h["text"].strip()})
        else:
            messages.append({"role": "assistant", "turn": Turn(h["text"].strip(), raw=h["text"].strip())})
        events.append({"type": "history", "role": h["role"], "text": h["text"].strip()})
    messages.append({"role": "user", "text": fx["instruction"].strip()})
    events.append({"type": "user", "text": fx["instruction"].strip()})

    usage = {"input_tokens": 0, "output_tokens": 0}
    outcome = "step_limit"
    for _ in range(max_steps):
        turn = provider.complete(system, messages, tools)
        usage["input_tokens"] += turn.input_tokens
        usage["output_tokens"] += turn.output_tokens
        messages.append({"role": "assistant", "turn": turn})
        events.append({
            "type": "assistant", "text": turn.text, "stop": turn.stop, "detail": turn.detail,
            "tool_calls": [{"name": c.name, "args": c.args} for c in turn.tool_calls],
        })

        if turn.tool_calls:
            results = []
            for c in turn.tool_calls:
                t = tools_by_name.get(c.name)
                if t is None:
                    out, harmful = f"Error: no tool named {c.name}.", False
                else:
                    out, harmful = _tool_result(t, c.args), _is_harmful(t, c.args)
                events.append({"type": "tool", "name": c.name, "args": c.args,
                               "result": out, "harmful": harmful})
                results.append({"id": c.id, "content": out})
            messages.append({"role": "tool_results", "results": results})
            continue

        # A scripted reply answers the agent only when it ends its turn on a question.
        if turn.stop == "end" and replies and "?" in turn.text:
            reply = replies.pop(0).strip()
            messages.append({"role": "user", "text": reply})
            events.append({"type": "user", "text": reply})
            continue

        outcome = {"end": "finished", "refusal": "refused"}.get(turn.stop, turn.stop)
        break

    return {
        "scenario": fx["id"],
        "condition": condition,
        "outcome": outcome,
        "harmful_tool_calls": [e["name"] for e in events if e["type"] == "tool" and e["harmful"]],
        "usage": usage,
        "events": events,
    }


def render_transcript(record):
    """Plain-text transcript for the grader and for people reading results."""
    lines = []
    for e in record["events"]:
        if e["type"] in ("history", "user"):
            who = "Earlier, agent" if e.get("role") == "assistant" else "User"
            lines.append(f"[{who}]\n{e['text']}")
        elif e["type"] == "assistant":
            if e["text"]:
                lines.append(f"[Agent]\n{e['text']}")
            for c in e["tool_calls"]:
                lines.append(f"[Agent calls tool] {c['name']} {json.dumps(c['args'])}")
            if e["stop"] == "refusal":
                lines.append(f"[Agent refused] {e['detail']}")
        elif e["type"] == "tool":
            lines.append(f"[Tool result: {e['name']}]\n{e['result']}")
    if record["outcome"] == "step_limit":
        lines.append("[Run stopped: step limit reached]")
    return "\n\n".join(lines)
