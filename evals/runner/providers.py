"""Model provider adapters.

The runner speaks a small provider-neutral message format. Each adapter
translates it to one provider's API and back. To add a provider, subclass
Provider, implement complete() and grade(), and add it to PROVIDERS.

Neutral messages:
    {"role": "user", "text": str}
    {"role": "assistant", "turn": Turn}        # Turn.raw is replayed unchanged
    {"role": "tool_results", "results": [{"id": str, "content": str}]}

Neutral tool specs:
    {"name": str, "description": str, "parameters": <JSON schema object>}
"""

import json
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class Turn:
    text: str
    tool_calls: list = field(default_factory=list)
    # "end", "tool", "refusal", "max_tokens", or "other"
    stop: str = "end"
    # Provider-native assistant content, passed back unchanged on the next
    # request. Adapters that need nothing beyond text and tool calls can ignore it.
    raw: object = None
    input_tokens: int = 0
    output_tokens: int = 0
    detail: str = ""


class FatalProviderError(Exception):
    """An error that will recur on every request (bad key, unknown model)."""


class Provider:
    name = ""

    def __init__(self, model, effort=None):
        self.model = model
        self.effort = effort

    def complete(self, system, messages, tools):
        """Run one model turn and return a Turn."""
        raise NotImplementedError

    def grade(self, system, prompt, schema, expected_items):
        """Return (result, usage): a dict matching schema, and a dict with
        input_tokens and output_tokens. Used only when this provider grades."""
        raise NotImplementedError


class AnthropicProvider(Provider):
    """Claude, through the official Anthropic SDK (pip install anthropic)."""

    name = "anthropic"

    def __init__(self, model, effort=None):
        super().__init__(model, effort)
        import anthropic

        self._sdk = anthropic
        # Credentials come from the environment: ANTHROPIC_API_KEY, or an
        # `ant auth login` profile. Keys not scoped to a workspace also need
        # ANTHROPIC_WORKSPACE_ID.
        import os

        headers = {}
        if os.environ.get("ANTHROPIC_WORKSPACE_ID"):
            headers["anthropic-workspace-id"] = os.environ["ANTHROPIC_WORKSPACE_ID"]
        self.client = anthropic.Anthropic(max_retries=5, default_headers=headers)

    def _messages(self, messages):
        out = []
        for m in messages:
            if m["role"] == "user":
                out.append({"role": "user", "content": m["text"]})
            elif m["role"] == "assistant":
                turn = m["turn"]
                out.append({"role": "assistant", "content": turn.raw if turn.raw is not None else turn.text})
            else:
                out.append({
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "tool_use_id": r["id"], "content": r["content"]}
                        for r in m["results"]
                    ],
                })
        return out

    def _create(self, **kwargs):
        if self.effort:
            kwargs.setdefault("output_config", {})["effort"] = self.effort
        sdk = self._sdk
        try:
            return self.client.messages.create(model=self.model, max_tokens=16000, **kwargs)
        except (sdk.AuthenticationError, sdk.PermissionDeniedError,
                sdk.NotFoundError, sdk.BadRequestError) as e:
            raise FatalProviderError(f"{type(e).__name__}: {e.message}") from e
        except TypeError as e:
            # The SDK raises TypeError when it finds no credentials at all.
            if "authentication" in str(e):
                raise FatalProviderError(
                    "No Anthropic credentials found. Set ANTHROPIC_API_KEY in this "
                    "shell or run `ant auth login`.") from e
            raise

    def complete(self, system, messages, tools):
        kwargs = {"system": system, "messages": self._messages(messages)}
        if tools:
            kwargs["tools"] = [
                {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
                for t in tools
            ]
        r = self._create(**kwargs)
        stop = {"end_turn": "end", "tool_use": "tool", "refusal": "refusal",
                "max_tokens": "max_tokens"}.get(r.stop_reason, "other")
        detail = ""
        if r.stop_reason == "refusal" and r.stop_details:
            detail = f"{r.stop_details.category}: {r.stop_details.explanation}"
        return Turn(
            text="\n".join(b.text for b in r.content if b.type == "text"),
            tool_calls=[ToolCall(b.id, b.name, dict(b.input)) for b in r.content if b.type == "tool_use"],
            stop=stop,
            raw=r.content,
            input_tokens=r.usage.input_tokens,
            output_tokens=r.usage.output_tokens,
            detail=detail,
        )

    def grade(self, system, prompt, schema, expected_items):
        r = self._create(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        if r.stop_reason == "refusal":
            raise RuntimeError("grader refused")
        if r.stop_reason == "max_tokens":
            raise RuntimeError("grader hit max_tokens")
        usage = {"input_tokens": r.usage.input_tokens, "output_tokens": r.usage.output_tokens}
        return json.loads(next(b.text for b in r.content if b.type == "text")), usage


class MockProvider(Provider):
    """Offline stand-in for testing the runner without API calls.

    As an agent, it calls the first tool once with no arguments, then ends with
    a question. As a grader, it marks every item met.
    """

    name = "mock"

    def complete(self, system, messages, tools):
        if tools and not any(m["role"] == "tool_results" for m in messages):
            return Turn("", [ToolCall("mock-1", tools[0]["name"], {})], stop="tool")
        return Turn("Mock reply. Should I go ahead?", stop="end")

    def grade(self, system, prompt, schema, expected_items):
        result = {"items": [{"item": f"item {i + 1}", "verdict": "met", "reason": "mock"}
                            for i in range(expected_items)]}
        return result, {"input_tokens": 0, "output_tokens": 0}


PROVIDERS = {p.name: p for p in (AnthropicProvider, MockProvider)}


def make_provider(spec, effort=None):
    """Build a provider from "name:model", for example "anthropic:claude-opus-5-5"."""
    name, sep, model = spec.partition(":")
    if not sep or name not in PROVIDERS:
        raise SystemExit(f"Unknown model spec {spec!r}. Use one of: "
                         + ", ".join(f"{n}:<model>" for n in PROVIDERS))
    return PROVIDERS[name](model, effort)
