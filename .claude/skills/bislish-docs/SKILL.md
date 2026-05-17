---
name: bislish-docs
description: >
  Add or update Python docstrings after code generation. Use this skill after writing
  any Python class, method, or function — triggered automatically as the final step of
  code generation, or when the user asks to "document this", "add docstrings", "add docs",
  or "document the code". Writes concise class-level and function-level docstrings in
  Bislish (Bisaya + English mix): technical jargon stays in English, Bisaya cues used
  naturally and sparingly — not forced on every line.
---

# Bislish Docstring Standard

Write **concise** Python docstrings for every class and non-trivial function.
The voice is Bislish — a natural mix of Bisaya and English. Technical terms
(ASR, WPM, Phil-IRI, Pydantic, pyright, Protocol, etc.) are always English.
Bisaya cues appear naturally, not on every sentence.

---

## Rules

### What to document
- Every class — one or two sentences on its single responsibility
- Every public method/function — what it does, any non-obvious behaviour, edge cases
- Skip `__init__` if the class docstring already explains it
- Skip trivial property getters — the type annotation says enough

### What NOT to do
- Don't restate the type annotations — they're already there
- Don't write `Args:` / `Returns:` sections (Google style) — too verbose for this project
- Don't document every param by name unless the name alone is unclear
- Don't force Bisaya on every sentence — use it where it sounds natural

### Length
- Class docstring: 1–3 sentences
- Method docstring: 1–2 sentences, 3 max for complex logic
- If the function name + types already tell the full story, one short line is enough

---

## Bisaya Cue Reference

Use these naturally and sparingly:

| Bisaya | Meaning | Example use |
|---|---|---|
| `kung` | if / when | "Returns 0.0 kung walay words." |
| `walay` | no / without | "Returns empty list kung walay alignment." |
| `para` | for / so that | "Para ma-classify ang each word." |
| `ug` | and | "Transcribes ug aligns ang audio." |
| `sa` | in / at / to | "Gi-save sa Supabase." |
| `gi-` prefix | done/past action | "Gi-align ang transcript sa passage." |
| `mo-` prefix | will / active | "Mo-raise og HTTPException kung invalid." |
| `pag-` | upon / when | "Pag-empty sa transcript, all words become omissions." |
| `mao ni` | this is / that's | "Mao ni ang entry point sa GO2 pipeline." |
| `dili` | not / don't | "Dili i-load per request — startup ra." |
| `bitaw` | right / indeed | "One class, one job bitaw." |

---

## Format

Use plain triple-quote docstrings — no Google/NumPy sections.

```python
class ScoringEngine:
    """
    Computes WPM, word recognition %, ug reading level gikan sa aligned transcript.

    Mao ni ang final step sa GO2 pipeline — pure arithmetic, no external deps.
    """

    def score(self, words: list[WordSegment], counts: MiscueCounts) -> ScoreResult:
        """Combines WPM ug word recognition into a ScoreResult."""

    def compute_wpm(self, words: list[WordSegment], total_words: int) -> float:
        """
        Computes words-per-minute from forced-alignment timestamps.

        Returns 0.0 kung walay words or kung negative ang duration.
        """

    def classify_reading_level(self, pct: float) -> ReadingLevel:
        """
        Maps word recognition % to Phil-IRI reading level.

        Boundary rule: exact ties go to the lower classification (e.g. 91.0 → Instructional,
        dili Independent).
        """
```

```python
class MiscueClassifier:
    """
    Gi-classify ang transcript words against Phil-IRI's 7 miscue categories.

    Uses SequenceMatcher to align transcript to passage, then labels each word:
    correct, mispronunciation, substitution, omission, insertion, repetition,
    or refusal_to_pronounce.
    """

    def classify(self, words: list[WordSegment], passage: str) -> MiscueCounts:
        """
        Returns miscue counts para sa entire passage.

        Pag-empty sa transcript, all passage words become omissions.
        """
```

```python
class AnalyzeController:
    """
    Handles HTTP for POST /analyze ug GET /health.

    Auth check, file I/O, ug service delegation ra — walay business logic diri.
    """

    async def analyze(self, ...) -> AssessmentResult:
        """
        Accepts a video upload, validates the API key, delegates to AnalyzeService.

        Mo-raise og 401 kung invalid ang X-API-Key.
        """
```

```python
class GO2Pipeline:
    """
    Orchestrates the GO2 audio pipeline: transcribe → classify → score.

    Mao ni ang sequencer — dili siya mag-implement sa bisan unsang step.
    """
```

---

## When to Run

This skill runs as the **last step** after `generate-and-verify` completes —
after pyright passes and SOLID check is clean. Add docstrings to the final file,
then show the documented version to the user for approval before writing.

If used standalone ("add docs to this file"), read the file first, add/update
docstrings on all public classes and methods, then show the result for approval.
