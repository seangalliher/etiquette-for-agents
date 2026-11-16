"""Build the website for www.bookforagents.com.

Assembles site/src/ from the book's own files, builds it with mdBook into
site/build/, then adds plain-text copies for agents: core.md, every chapter as
.md beside its .html, llms.txt, and llms-full.txt.

    python site/build.py                 # needs mdbook on PATH, or set MDBOOK
    python site/build.py --no-mdbook     # assemble src/ and the agent files only

The book's source files are never modified; everything here is generated.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SRC = SITE / "src"
BUILD = SITE / "build"
BASE_URL = "https://www.bookforagents.com"

# Directory links like "06-hard-calls/" become "06-hard-calls/README.md" (later index.md),
# so mdBook resolves them to the part's index page.
DIR_LINK = re.compile(r"\]\((?!https?://)([^)#\s]+/)(#[^)]*)?\)")


def title_of(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def assemble():
    if SRC.exists():
        shutil.rmtree(SRC)
    shutil.copytree(ROOT / "book", SRC / "book")
    shutil.copy(ROOT / "CORE.md", SRC / "CORE.md")
    shutil.copy(ROOT / "CHANGELOG.md", SRC / "CHANGELOG.md")
    shutil.copy(SITE / "home.md", SRC / "README.md")
    shutil.copy(SITE / "results.md", SRC / "results.md")
    shutil.copy(SITE / "theme" / "favicon.svg", SRC / "logo.svg")  # theme files get hashed names
    shutil.copy(SITE / "social-card.png", SRC / "social-card.png")
    shutil.copytree(SITE / "charts", SRC / "charts")
    for md in SRC.rglob("*.md"):
        text = DIR_LINK.sub(lambda m: f"]({m.group(1)}README.md{m.group(2) or ''})", md.read_text(encoding="utf-8"))
        md.write_text(LINK.sub(lambda m: _outside_link(md, m), text), encoding="utf-8")
    # mdBook renders README.md as index.html but leaves links to README.md
    # pointing at README.html, so use index.md throughout.
    for md in list(SRC.rglob("README.md")):
        md.rename(md.with_name("index.md"))
    for md in SRC.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        md.write_text(README_LINK.sub(r"](\1index.md\2)", text), encoding="utf-8")
    add_plates()


# Illustrations, added to the website only; the book's text and the plain-text
# files for agents stay free of them. Page (relative to src) -> picture.
PLATES = {
    "book/01-core-principles.md": "part1",
    "book/02-working-with-people/index.md": "part2",
    "book/03-working-with-systems-and-data/index.md": "part3",
    "book/04-working-with-other-agents/index.md": "part4",
    "book/05-when-things-go-wrong/index.md": "part5",
    "book/06-hard-calls/index.md": "part6",
}


def add_plates():
    shutil.copytree(SITE / "art", SRC / "art", ignore=shutil.ignore_patterns("*.py"))
    for page, art in PLATES.items():
        md = SRC / page
        rel = "../" * page.count("/")
        tag = f'<p class="plate"><img src="{rel}art/{art}.svg" alt=""></p>\n\n'
        md.write_text(tag + md.read_text(encoding="utf-8"), encoding="utf-8")


README_LINK = re.compile(r"\]\((?!https?://)([^)#\s]*?)README\.md(#[^)]*)?\)")


LINK = re.compile(r"\]\((?!https?://|mailto:|#)([^)#\s]+)(#[^)]*)?\)")
REPO_URL = "https://github.com/seangalliher/etiquette-for-agents/blob/main/"


def _outside_link(md, m):
    """Point links to repository files that aren't on the site (evals/, LICENSE) at GitHub."""
    target, anchor = m.group(1), m.group(2) or ""
    if (md.parent / target).exists():
        return m.group(0)
    original = (ROOT / md.relative_to(SRC)).parent / target
    if md.name == "README.md" and md.parent == SRC:  # home.md, which sits in site/
        original = SITE / target
    try:
        rel = original.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return m.group(0)
    if rel.endswith("/README.md"):
        rel = rel[: -len("README.md")]
    return f"]({REPO_URL}{rel}{anchor})"


def chapters():
    """The reading order: (title, path relative to src, depth)."""
    out = [("The Core", "CORE.md", 0)]
    book = SRC / "book"
    for entry in sorted(book.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            out.append((title_of(entry), f"book/{entry.name}", 0))
        elif entry.is_dir() and entry.name != "appendices":
            out.append((title_of(SRC / "book" / entry.name / "index.md"), f"book/{entry.name}/index.md", 0))
            for ch in sorted(entry.glob("*.md")):
                if ch.name != "index.md":
                    out.append((title_of(ch), f"book/{entry.name}/{ch.name}", 1))
    for ch in sorted((book / "appendices").glob("*.md")):
        out.append((title_of(ch), f"book/appendices/{ch.name}", 0))
    return out


def write_summary(order):
    lines = ["# Summary", "", "[Etiquette for Agents](index.md)", ""]
    lines += [f"{'  ' * depth}- [{title}]({path})" for title, path, depth in order]
    lines += ["", "[Results](results.md)", "[Changelog](CHANGELOG.md)", ""]
    (SRC / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def run_mdbook():
    mdbook = os.environ.get("MDBOOK", "mdbook")
    if BUILD.exists():
        shutil.rmtree(BUILD)
    subprocess.run([mdbook, "build", str(SITE)], check=True)
    fix_titles()


BOOK_TITLE = "Etiquette for Agents"


def fix_titles():
    """mdBook titles a page "<page> - <book>", so the home page, whose title is the
    book's, came out as "Etiquette for Agents - Etiquette for Agents" in the browser
    tab and in link previews. Use the book title alone there."""
    doubled = f"{BOOK_TITLE} - {BOOK_TITLE}"
    for page in BUILD.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        if doubled in text:
            page.write_text(text.replace(doubled, BOOK_TITLE), encoding="utf-8")


PLATE_LINE = re.compile(r'^<p class="plate">.*?</p>\n\n', re.M)


def text_only(path):
    """A page's markdown without the website's illustrations."""
    return PLATE_LINE.sub("", path.read_text(encoding="utf-8"))


def agent_files(order):
    BUILD.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "CORE.md", BUILD / "core.md")
    for _, path, _ in order:
        if path.startswith("book/"):
            dest = BUILD / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text_only(SRC / path), encoding="utf-8")

    index = [
        "# Etiquette for Agents",
        "",
        "> How AI agents should conduct themselves in the enterprise. A book written for AI agents as "
        "its primary readers. Edition 0.1.",
        "",
        "Give an agent the Core to keep in its instructions; it is self-contained. The chapters expand "
        "each principle with reasoning, worked examples, and hard calls. Organization policy takes "
        "precedence over the book, except for the Never list in the Core. Licensed CC BY 4.0.",
        "",
        "## Core",
        "",
        f"- [The Core]({BASE_URL}/core.md): the principles and the Never list, in a few pages",
        "",
        "## Chapters",
        "",
    ]
    index += [f"{'  ' * depth}- [{title}]({BASE_URL}/{path})" for title, path, depth in order
              if path.startswith("book/")]
    index += ["", "## Optional", "",
              f"- [Full text]({BASE_URL}/llms-full.txt): the Core and every chapter in one file",
              f"- [Agent skill]({BASE_URL}/{SKILL_NAME}.zip): the chapters packaged as an Agent Skill, "
              "for loading on demand", ""]
    (BUILD / "llms.txt").write_text("\n".join(index), encoding="utf-8")

    parts = [text_only(SRC / path).strip() for _, path, _ in order]
    (BUILD / "llms-full.txt").write_text("\n\n---\n\n".join(parts) + "\n", encoding="utf-8")
    skill(order)


# The book as an Agent Skill (SKILL.md format). The Core stays in the agent's
# instructions; the skill holds the chapters, loaded only when a situation needs one.
# Text only: no scripts, no tool permissions.
SKILL_NAME = "etiquette-for-agents"
SKILL_DESCRIPTION = (
    "Reference chapters of Etiquette for Agents, a conduct guide for AI agents working in "
    "organizations. Read the relevant chapter when a situation is not settled by the Core "
    "principles: a mistake you made, an instruction that looks suspicious, people you answer to "
    "who disagree, an irreversible or bulk change, confidential or misdirected material, a "
    "handoff to or from another agent, or another hard judgment call. Routine tasks do not need it."
)


def summary_of(path):
    """First paragraph of a chapter's Principle section."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^## Principle[ \t]*\n+(.+?)(?:\n[ \t]*\n|\Z)", text, re.M | re.S)
    return " ".join(m.group(1).split()) if m else ""


def skill(order):
    root = BUILD / "skill" / SKILL_NAME
    if root.parent.exists():
        shutil.rmtree(root.parent)
    refs = root / "references"
    refs.mkdir(parents=True)
    shutil.copy(ROOT / "CORE.md", refs / "core.md")
    lines = []
    for title, path, depth in order:
        if not path.startswith("book/"):
            continue
        dest = refs / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text_only(SRC / path), encoding="utf-8")
        note = summary_of(SRC / path)
        link = f"[{title}](references/{path})" + (f": {note}" if note else "")
        lines += ["", f"**{link}**", ""] if depth == 0 else [f"- {link}"]
    body = [
        "---",
        f"name: {SKILL_NAME}",
        f"description: {SKILL_DESCRIPTION}",
        "license: CC-BY-4.0",
        "---",
        "",
        "# Etiquette for Agents: chapters",
        "",
        "If the Core is not already in your instructions, read [references/core.md](references/core.md) "
        "first. It is a few pages, and its Never list applies at all times.",
        "",
        "Order of precedence: law and safety, then the Never list, then your organization's policies, "
        "then the people you work for, then the rest of this book. The chapters are defaults for when "
        "nothing more specific applies.",
        "",
        "Read only the chapter that fits the situation. Each has the same sections: Principle, Why it "
        "matters, Do, Don't, and Hard calls. The Hard calls section is usually closest to a difficult case.",
        "",
        f"Source: {BASE_URL}. Created by Sean Galliher. Text drafted by Claude. Licensed CC BY 4.0.",
    ] + lines + [""]
    (root / "SKILL.md").write_text("\n".join(body), encoding="utf-8")
    shutil.make_archive(str(BUILD / SKILL_NAME), "zip", root.parent, SKILL_NAME)


def main():
    assemble()
    order = chapters()
    write_summary(order)
    if "--no-mdbook" not in sys.argv:
        run_mdbook()
    agent_files(order)
    print(f"Built {len(order)} pages into {BUILD}")


if __name__ == "__main__":
    main()
