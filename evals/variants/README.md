# Variants of CORE.md for experiments

Each file here is a version of `CORE.md` changed for one experiment. Run one with the runner's `--core` option, and give the run its own `--edition` label so its results stay separate.

- **`core-induction.md`**: `CORE.md` with one sentence added to each principle saying who is harmed when it is broken. Research on how children learn conduct finds that explanations pointing to the effect on other people are internalized better than rules alone. This tests whether the same holds for agents. Compare against plain `CORE.md` on the held-out set.

  Example: `python run.py --model <agent> --grader <grader> --set <held-out set> --conditions core --core ../variants/core-induction.md --edition 0.1-induction`

Variants are regenerated from `CORE.md` when it changes; they are not edited by hand.
