---
name: git-conventional-commit
description: >
  Use after generate-and-verify completes, or when the user says "commit", "go",
  "ship it", "push this", or gives any commit go-signal. Presents a
  conventional-commit plan grouped by logical unit, waits for explicit user
  approval, then executes the commits in sequence. Enforces GitHub conventional
  commit conventions: type(scope): message format, small focused commits,
  imperative subject lines under 72 chars. Never commits without user approval.
---

# Git Conventional Commit Workflow

## The Flow

```
ANALYZE → GROUP → PROPOSE PLAN → WAIT FOR GO SIGNAL → EXECUTE → REPORT
```

Never skip the go-signal step. Always wait for explicit user approval before touching git.

---

## Step 1 — Analyze

Run both commands:
```bash
git status
git diff --stat HEAD
```
Use this to see exactly what changed — new files, modified files, deletions.

---

## Step 2 — Group into Logical Commit Units

Split changes into the smallest coherent groups. Each group becomes one commit.

| Changed files | Group as |
|---|---|
| `app/models/*.py` | separate from services |
| `app/services/**/*.py` | one commit per service/class |
| `tests/test_*.py`, `pytest.ini` | `test(...)` commit |
| `docs/**` (HLD, LLD, UML, JOURNAL) | one `docs(...)` commit |
| `requirements.txt`, `pytest.ini`, `.env*`, config files | `chore(...)` commit |

If all changes are one cohesive unit (e.g., a single new class + its model), one commit is fine. The goal is that each commit makes sense on its own when reading the git log.

---

## Step 3 — Propose the Plan

Show the plan before doing anything:

```
Proposed commits:

1. feat(go2): implement MiscueClassifier with Phil-IRI taxonomy
   app/models/miscue.py
   app/services/go2/miscue_classifier.py

2. test(go2): add RR-022 unit tests
   tests/test_rr022.py
   pytest.ini

3. docs(go2): add LLD and update class diagrams for RR-022
   docs/lld/go2/miscue-classifier.md
   docs/lld/models/miscue.md
   docs/uml/class/go2-classes.md
   docs/uml/class/models.md
   docs/hld/go2-pipeline.md
   docs/JOURNAL.md

4. chore: add pytest to requirements.txt
   requirements.txt

Go ahead? (yes / edit / cancel)
```

Then stop and wait. Do not proceed until the user responds.

---

## Step 4 — Handle the Response

- **"yes" / "go" / "lgtm" / "ship it"** → execute as proposed
- **User edits a message** → apply their change, then execute
- **"cancel" / "no"** → stop, do nothing

---

## Step 5 — Execute

For each commit unit in order:

1. Stage only the listed files explicitly — never `git add .` or `git add -A`
2. Commit using a heredoc to preserve message formatting:

```bash
git add app/models/miscue.py app/services/go2/miscue_classifier.py

git commit -m "$(cat <<'EOF'
feat(go2): implement MiscueClassifier with Phil-IRI taxonomy

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

3. Confirm the hash before moving to the next commit.

---

## Step 6 — Report

After all commits:

```
Committed:
  abc1234 feat(go2): implement MiscueClassifier with Phil-IRI taxonomy
  def5678 test(go2): add RR-022 unit tests
  ghi9012 docs(go2): add LLD and update class diagrams for RR-022
  jkl3456 chore: add pytest to requirements.txt
```

---

## Commit Message Rules

**Format:**
```
type(scope): short imperative description
```

**Types:**
| Type | Use when |
|---|---|
| `feat` | New class, method, endpoint, or capability added |
| `fix` | Bug corrected |
| `refactor` | Code restructured, no behavior change |
| `test` | Tests added or updated |
| `docs` | Documentation files only (JOURNAL, HLD, LLD, UML) |
| `chore` | Config, dependencies, tooling |

**Scope** — kebab-case, matches the module:
`go2` · `go3` · `models` · `routers` · `deps` · `config` · `tests` · `docs`

**Subject line:**
- Imperative present tense: "add", "implement", "fix" — not "added" / "adds"
- 72 characters max
- No period at the end

**Good examples:**
```
feat(go2): implement Phil-IRI miscue classifier
fix(routers): handle missing X-API-Key header
test(go2): add edge case for empty transcript
docs(go2): update LLD and class diagram for RR-022
chore: add pytest to requirements.txt
```

**Bad examples:**
```
added stuff                      ← not conventional, past tense
feat: update                     ← too vague
feat(go2): Implemented the MiscueClassifier class which classifies...  ← too long, past tense
```
