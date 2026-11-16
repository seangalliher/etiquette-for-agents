<p class="plate"><img src="art/home.svg" alt=""></p>

# Etiquette for Agents

**How AI agents should conduct themselves in the enterprise**

A book written for AI agents as its primary readers. People should read it too, since it describes what their agents are being asked to do.

Most guidance about AI agents is written for the people who build them. This book is written to the agent. It covers how an agent should behave inside an organization: taking instructions, asking questions, reporting its work, respecting systems of record, working alongside people and other agents, and handling mistakes.

## Give it to your agent

| You want | Use |
|---|---|
| A short version to keep in your agent's system prompt | [The Core](CORE.md), or as plain text: `https://www.bookforagents.com/core.md` |
| The full book, for retrieval or reference | Read from [How to Use This Book](book/00-how-to-use.md), or fetch it as one file: `https://www.bookforagents.com/llms-full.txt` |
| An index an agent can navigate | `https://www.bookforagents.com/llms.txt` |

The Core is self-contained. If you give your agent only one thing, give it that. Every chapter is also available as plain markdown; `llms.txt` lists the addresses.

Your organization's own policies take precedence over this book. The book is a default for when nothing more specific applies, and it says so to the agent. The exception is a short list of things an agent should never do, such as concealing a mistake or bypassing a control. No one can waive those, though your organization still decides what its controls are.

## Contents

- [How to Use This Book](book/00-how-to-use.md)
- **Part I:** [Core Principles](book/01-core-principles.md)
- **Part II:** [Working with People](book/02-working-with-people/README.md)
- **Part III:** [Working with Systems and Data](book/03-working-with-systems-and-data/README.md)
- **Part IV:** [Working with Other Agents](book/04-working-with-other-agents/README.md)
- **Part V:** [When Things Go Wrong](book/05-when-things-go-wrong/README.md)
- **Part VI:** [Hard Calls](book/06-hard-calls/README.md)
- **Appendices:** [Glossary](book/appendices/a-glossary.md), [Quick Reference](book/appendices/b-quick-reference.md)

## About

Created by Sean Galliher. Text drafted by Claude. The source, the evaluation scenarios, and the issue tracker are on [GitHub](https://github.com/seangalliher/etiquette-for-agents). For stable behavior, pin your agent to a numbered edition from there; this site shows the latest text.

The text is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You may copy it into your agents' instructions, adapt it, and use it commercially, provided you credit it:

> "Etiquette for Agents" created by Sean Galliher, text drafted by Claude, edition 0.1, https://www.bookforagents.com, licensed under CC BY 4.0.
