---
name: dev-journal
description: >
  Append a concise journal entry to docs/JOURNAL.md after each code generation
  iteration. Tracks what was built, what changed, and any key decisions made.
  Use after every generate-and-verify cycle, or when the user asks to "log this",
  "journal this", "track this change", "write it down", or "update the changelog".
  One entry per iteration — never rewrite existing entries.
---

# Dev Journal Skill

After each iteration, append one entry to `docs/JOURNAL.md`. The journal is
append-only — existing entries are never edited or deleted. It is a permanent
record of what was built and why.

---

## Entry Format

```markdown
---

### YYYY-MM-DD · Iteration N — <short title>

**Added**
- `path/to/file.py` — one line on what it does

**Changed**
- `path/to/file.py` — what changed and why

**Removed**
- `path/to/file.py` — why it was removed

**Design Decisions**
- <decision> — <reason>

**Verification**
- Pyright: `0 errors`
- SOLID: ✓ / ⚠ `<note if any violation was found and fixed>`
- Docs: `hld/<file>.md`, `lld/<domain>/<file>.md`, `uml/<type>/<file>.md`
```

---

## Rules

- **One entry per generate-and-verify iteration** — not one per file
- **Concise** — bullet points only, no paragraphs
- **Added / Changed / Removed** — only include sections that apply; skip empty ones
- **Design Decisions** — only log non-obvious choices (e.g. why Protocol over ABC,
  why TypedDict over dataclass for a specific shape). Skip obvious ones.
- **Iteration N** — increment from the last entry in the file; start at 1 if the
  file is new
- **Short title** — name of the feature, class, or task (e.g. `GO2 Scaffold`,
  `MiscueClassifier`, `Stub /analyze endpoint`)

---

## File Location

`docs/JOURNAL.md` — in the project root `docs/` folder.

If the file does not exist yet, create it with this header first:

```markdown
# Dev Journal — ReadRight GO2

> Append-only log of each build iteration. Newest entries at the bottom.

---
```

Then append the first entry below the header.

---

## When to Run

This is the **last step** in the generate-and-verify loop — after docstrings and
design docs are written. Append the entry, then include it in the final report
so the user sees what was logged.

Do not show the journal entry for approval — it is a log, not code. Just write it.
