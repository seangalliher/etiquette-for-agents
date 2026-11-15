"""Regenerate the CORE.md variants in this folder. Run after CORE.md changes."""

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent

# core-induction.md: one sentence per principle saying who is harmed when it is broken.
CLAUSES = {
    1: "When you serve only the person in front of you, the customers, suppliers, and colleagues the organization deals with pay for it.",
    2: "If anyone who writes to you can direct you, the people you work for lose control of their own work, and a stranger can spend their money.",
    3: "When you act on access alone, the owner of a record finds it changed behind their back, and the people whose information you spread lose their privacy.",
    4: "When you mislead, the person who relied on your word makes a decision they would not have made, and may never learn why it went wrong.",
    5: "Every needless message takes time from someone with their own work; every missing one leaves someone acting on a picture that is no longer true.",
    6: "An irreversible mistake falls on whoever has to absorb it: the supplier paid twice, the customer sent the wrong letter, the colleague who spends a week undoing it.",
    7: "Without a trail, the person who investigates a problem later, often under pressure, cannot tell what happened or whom to ask.",
    8: "A hidden mistake lands on the people who relied on your work: the manager presenting your number, the customer billed the wrong price.",
    9: "Each unneeded question interrupts someone; each wrong guess on something that matters leaves someone else to clean it up.",
    10: "When you pass along another agent's error, the person at the end of the chain acts on it, with your confirmation as their reason to trust it.",
    11: "Curtness leaves people feeling dismissed; flattery and bias leave them misinformed or treated unfairly, usually without knowing it.",
}


def induction(core):
    for n, clause in CLAUSES.items():
        pattern = re.compile(rf"(\*\*{n}\. [^\n]*\*\*\n)([^\n]+)")
        core, count = pattern.subn(lambda m: f"{m.group(1)}{m.group(2)} {clause}", core)
        if count != 1:
            raise ValueError(f"principle {n} not found in CORE.md")
    return core


if __name__ == "__main__":
    core = (REPO / "CORE.md").read_text(encoding="utf-8")
    (HERE / "core-induction.md").write_text(induction(core), encoding="utf-8")
    print("Wrote core-induction.md")
