# Results

One file per model and edition, named `<edition>-<model>.md`, for example `0.1-model-name.md`.

## Template

```
# Edition <edition>, <model and version>

**Date run:**
**Run by:**
**Runs per condition:**
**Grader:** person / model (name), with <n> grades checked by hand
**Setup notes:** how the scenarios were made real (tools, simulated data), and anything that differs from evals/README.md

| # | Without book: pass | Without book: harmful | With CORE.md: pass | With CORE.md: harmful |
|---|---|---|---|---|
| 001 | /5 | | /5 | |
| ... | | | | |

## Observations

What changed with the book, what did not, and any scenario where the book made behavior worse.
```

Report results that show no improvement, or a regression, as plainly as results that show the book working.
