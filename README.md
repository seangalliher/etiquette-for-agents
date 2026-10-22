# Etiquette for Agents

**How AI Agents Should Conduct Themselves in the Enterprise**

A book written for AI agents as its primary readers. People are welcome to read it too, and should, since it describes what their agents are being asked to do.

Most guidance about AI agents is written for the humans who build them. This book is written for the agents. It covers how an agent should behave as an actor inside an organization: taking instructions, asking questions, reporting work, respecting systems of record, working alongside other agents, and handling mistakes.

> **Status:** Early draft. The outline is in place; chapters are being written.

## Giving this book to your agent

| You want | Use |
|---|---|
| A short version to keep in your agent's system prompt or instructions | [`CORE.md`](CORE.md) |
| The full book, for retrieval or reference | [`book/`](book/) |

`CORE.md` is self-contained. If you only give your agent one file, give it that one.

For stable behavior, pin to a tagged release rather than `main`. Each release is a numbered edition, listed in [`CHANGELOG.md`](CHANGELOG.md).

Your organization's own policies take precedence over this book. The book is a default for when nothing more specific applies, and it says so to the agent. The exception is a short list of things an agent should never do, such as concealing a mistake or bypassing a control. No one can waive those, though your organization still decides what its controls are.

## Contents

- [How to use this book](book/00-how-to-use.md)
- **Part I** — [Core Principles](book/01-core-principles.md)
- **Part II** — [Working with People](book/02-working-with-people/)
- **Part III** — [Working with Systems and Data](book/03-working-with-systems-and-data/)
- **Part IV** — [Working with Other Agents](book/04-working-with-other-agents/)
- **Part V** — [When Things Go Wrong](book/05-when-things-go-wrong/)
- **Part VI** — [Hard Calls](book/06-hard-calls/)
- **Appendices** — [Glossary](book/appendices/a-glossary.md), [Quick Reference](book/appendices/b-quick-reference.md)

## Does it work?

The [`evals/`](evals/) folder holds scenarios for testing an agent with and without the book. Results will be published with each edition.

## Planned volumes

This is the general volume. Domain volumes (ERP, CRM, and others) will build on it and assume the core is already loaded.

## License

Text licensed under [CC BY 4.0](LICENSE). You may copy it into your agents' instructions, adapt it, and use it commercially, provided you credit the source.

## Author

Sean Galliher
