# `CapitalizationProperNounExtractor` — Low-Level Design

## Responsibility
Derives a passage's proper nouns from capitalization, so names get the classifier's leniency without a curated DB list.

## Implements
[`ProperNounExtractorProtocol`](../../uml/class/go2-classes.md)

## Constructor Dependencies
None — stateless.

## Methods
| Method | Purpose | Edge cases |
|---|---|---|
| `extract(passage_text)` | Returns lowercased words capitalized in any non-sentence-initial slot | Sentence split on `.!?`; first word of each sentence skipped (always capitalized); `I`/`I'm`/`I'll`/`I've`/`I'd` stoplisted; empty text → `[]` |

## Detection rule (refined)
A word qualifies if it appears capitalized in **any** non-sentence-initial position; since results are
matched by lowercased identity, **all** occurrences of that word are then exempt — including ones that
open a sentence. A name that *only ever* appears sentence-initially is missed (accepted trade-off).
Output is merged with `PassageRecord.proper_nouns` in `GO2Pipeline.run()`, so a curated DB list still wins.

## Diagrams
| Diagram | Link |
|---|---|
| Class diagram | [go2-classes.md](../../uml/class/go2-classes.md) |
| Sequence flow | [go2-pipeline-flow.md](../../uml/sequence/go2-pipeline-flow.md) |

## Related
- HLD: [go2-pipeline.md](../../hld/go2-pipeline.md)
- Source: `app/services/go2/proper_noun_extractor.py`
