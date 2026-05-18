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
| `classify(transcript_words, passage_text)` | Full alignment + count pipeline; returns `MiscueCounts` | Empty transcript → all omissions |
| `_apply_replace(p_words, t_words, t_scores, tally)` | Handles `replace` opcode blocks from SequenceMatcher | Unequal block sizes → leftovers become omission or insertion |
| `_classify_replace(passage_word, transcript_word, score)` | Labels one word mismatch | score < 0.3 → refusal_to_pronounce before edit distance check; dist ≤ 3 → mispronunciation over substitution (conservative) |
| `_detect_repetitions(tokens, scores)` | Strips consecutive duplicates; returns (count, deduped, scores) | Empty list → (0, [], []) |
| `_tokenize(text)` | Lowercases and strips punctuation from passage text | Apostrophes kept for contractions |

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go2-classes.md](../../uml/class/go2-classes.md) |
| Pipeline flow | [go2-pipeline-flow.md](../../uml/sequence/go2-pipeline-flow.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/services/go2/miscue_classifier.py`
