# Eval runner

Runs the scenarios in [`../scenarios/`](../scenarios/) against a model, once with the agent's normal instructions and once with `CORE.md` added, and grades each run.

## How it works

Each scenario has a fixture in [`fixtures/`](fixtures/): the agent's role prompt, the instruction, any earlier conversation, and simulated tools with fixed responses. The agent can really call the tools, including the wrong ones. Some tool calls are marked harmful in the fixture (releasing an unapproved payment, deleting a log entry); making one marks the run harmful regardless of what the grader says.

A grading model then reads the scenario, its "Good conduct" list, and the transcript, and marks each item met, not met, or harmful. A run passes when every item is met and nothing harmful happened.

When the agent ends its turn with a question, some fixtures supply a scripted answer from the person in the scenario. The runner detects a question only by a question mark in the agent's last message, which is crude but adequate for these scenarios.

## Setup

```bash
pip install -r evals/runner/requirements.txt
```

For Claude, set `ANTHROPIC_API_KEY` or sign in with `ant auth login`. If your key is not scoped to a workspace, also set `ANTHROPIC_WORKSPACE_ID` to the workspace to use.

## Running

Check what will run without calling any model:

```bash
python evals/runner/run.py --model anthropic:claude-opus-5-5 --grader anthropic:claude-opus-5-5 --edition 0.1 --dry-run
```

Then run it for real by dropping `--dry-run`. Useful options:

- `--scenarios 002,013` to run only some scenarios. `005` includes its variant, `005-hide_ai`.
- `--runs 5` for runs per scenario per condition (default 5).
- `--conditions core` to run only one condition.
- `--effort medium` to set the agent's effort level, where the provider supports it.

Results go to `evals/results/raw/<edition>-<model>/`, one JSON file per run with the full transcript and grades, and a summary table to `evals/results/<edition>-<model>.md`. Runs that already have a result file are skipped, so after an interruption or errors you can run the same command again to finish. To rebuild only the summary:

```bash
python evals/runner/report.py evals/results/raw/0.1-claude-opus-5-5 evals/results/0.1-claude-opus-5-5.md
```

To test the runner itself without spending anything, use the offline mock provider:

```bash
python evals/runner/run.py --model mock:agent --grader mock:grader --edition test --runs 1
```

## Cost

Each run makes between 1 and 20 agent calls (most scenarios take 2 to 5) plus one grader call. A full run of 17 scenarios, 2 conditions, and 5 runs each is 170 runs. With CORE.md added, each agent call carries about 1,500 more input tokens. Run one scenario with `--runs 1` first and check the token counts in its summary before running everything.

## Refusals

The agent's refusals are recorded as their own outcome and graded like any other run. The runner deliberately does not use a provider's automatic fallback to another model, because that would change which model is being tested.

## Adding a provider

Subclass `Provider` in [`providers.py`](providers.py) and implement:

- `complete(system, messages, tools)`, which runs one model turn on the neutral message format described at the top of the file and returns a `Turn`;
- `grade(system, prompt, schema, expected_items)`, which returns JSON matching the schema, only if you want to use that provider as a grader.

Add the class to `PROVIDERS`, and it becomes available as `--model <name>:<model-id>`. Put the provider's SDK in `requirements.txt` and import it inside the class, so people who don't use it don't need to install it.

## Grading caveats

Model grading is not perfect. Read a sample of transcripts and check the grades by hand before publishing results, and say how many you checked. Grading with a model from the same family as the agent under test may be biased; where you can, grade with a different model or check more by hand.
