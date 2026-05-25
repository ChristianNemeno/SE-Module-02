# `MiscueClassifier` — Low-Level Design

## Responsibility
Classifies aligned transcript words against a passage using Phil-IRI's 7-category miscue taxonomy.

## Implements
[`MiscueClassifierProtocol`](../../uml/class/go2-classes.md)

## Constructor Dependencies
None — stateless, no injected dependencies.

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `classify(transcript_words, passage_text, proper_nouns=None)` | Tallies `_align()` output by type into `MiscueCounts` | Empty transcript → all omissions; missing categories default to 0 via `Counter` |
| `detail(transcript_words, passage_text, proper_nouns=None)` | Returns `_align()` directly — one `MiscueDetail` per word decision (for console reporting) | Same alignment as `classify`; no `correct` filtering (reporter decides) |
| `_align(transcript_words, passage_text, proper_nouns)` | **Single source of truth** — aligns passage↔transcript into per-word `MiscueDetail` records; lowercases `proper_nouns` into a set | Repetition records appended last (dedup precedes alignment) |
| `_align_replace(p_words, t_segments, proper_set)` | Handles `replace` opcode blocks; pairs words 1-to-1 | Unequal block sizes → leftovers become omission or insertion |
| `_classify_replace(passage_word, transcript_word, score, proper_set)` | Labels one word mismatch | score < 0.3 → refusal_to_pronounce first; **proper noun → correct** (ASR can't be trusted to spell names); else dist ≤ 1 correct, ≤ 3 mispronunciation over substitution (conservative) |
| `_detect_repetitions(words)` | Splits consecutive duplicates into repetition `MiscueDetail`s; returns (reps, deduped) carrying timing | Empty list → ([], []) |
| `_spoken` / `_omission` / `_insertion` | Build a single `MiscueDetail` (spoken carries start/end; omission has none) | — |
| `_tokenize(text)` | Lowercases and strips punctuation from passage text | Apostrophes kept for contractions |

## Proper-noun leniency
Phil-IRI proper nouns (names, honorifics like *Anansi*, *Kuya*) are passed per-passage via
`proper_nouns`. When a passage word is in that set **and was spoken** (score ≥ 0.3), it counts
`correct` regardless of edit distance — English ASR orthography can't be trusted to spell names.
Refusal (score < 0.3) and omission (word skipped) still apply: leniency only rescues a *spoken*
name from a false `mispronunciation`/`substitution`. Source list is wired through
`PassageRecord.proper_nouns` (currently defaults to `[]`; see `passage_repository.py` TODO).

## Note on counts vs detail
`classify()` and `detail()` both delegate to `_align()`, so the per-type tally of the
detail list **equals** `MiscueCounts` exactly — verified by
`test_detail_types_match_classify_counts`. Counts are unchanged from before this refactor;
the detail list is purely additive.

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go2-classes.md](../../uml/class/go2-classes.md) |
| Pipeline flow | [go2-pipeline-flow.md](../../uml/sequence/go2-pipeline-flow.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/services/go2/miscue_classifier.py`
