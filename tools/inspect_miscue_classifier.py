"""Run the GO2 miscue classifier against the pre-computed transcription CSVs.

Reads the recordings' WhisperX transcripts from `tests/fixtures/audio/transcriptions/`
and the original passage text from `tests/fixtures/passages/`, builds WordSegments,
and prints the classifier output + Phil-IRI scoring for each pair.

Usage:
    python tools/inspect_miscue_classifier.py                          # all 7 passages, both variants
    python tools/inspect_miscue_classifier.py --passage 3              # passage 3, both variants
    python tools/inspect_miscue_classifier.py --passage 3 --variant incorrect
    python tools/inspect_miscue_classifier.py --only-miscues           # hide the per-event 'correct' lines (default)
    python tools/inspect_miscue_classifier.py --show-correct           # print every aligned event
"""
from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from pathlib import Path

# Allow running as a script: add repo root so `from app...` resolves.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.miscue import MiscueDetail  # noqa: E402
from app.models.transcription import WordSegment  # noqa: E402
from app.services.go2.miscue_classifier import MiscueClassifier  # noqa: E402
from app.services.go2.proper_noun_extractor import CapitalizationProperNounExtractor  # noqa: E402
from app.services.go2.scoring_engine import ScoringEngine  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PASSAGE_DIR = _REPO_ROOT / "tests" / "fixtures" / "passages"
_TRANSCRIPT_DIR = _REPO_ROOT / "tests" / "fixtures" / "audio" / "transcriptions"
_WORD_RE = re.compile(r"[a-zA-Z']+")
_ERROR_TYPES = frozenset({"mispronunciation", "substitution", "omission", "insertion", "repetition"})


def _load_passage(passage_n: int) -> str:
    """Read passage{n}.txt from the fixture directory."""
    return (_PASSAGE_DIR / f"passage{passage_n}.txt").read_text(encoding="utf-8").strip()


def _passage_word_count(text: str) -> int:
    """Count whole tokens in the passage — same regex used by the classifier."""
    return len(_WORD_RE.findall(text))


def _load_transcript(passage_n: int, variant: str) -> list[WordSegment]:
    """Load a WhisperX-shaped CSV into WordSegment dicts."""
    csv_path = _TRANSCRIPT_DIR / f"passage{passage_n}{variant}.transcription.csv"
    words: list[WordSegment] = []
    with csv_path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            words.append(
                WordSegment(
                    word=row["word"].lower().strip(),
                    start=float(row["start"]),
                    end=float(row["end"]),
                    score=float(row["score"]) if row.get("score") else 1.0,
                )
            )
    return words


def _format_detail(d: MiscueDetail) -> str:
    """Render one MiscueDetail event for the console."""
    passage = repr(d["passage_word"]) if d["passage_word"] is not None else "—"
    heard = repr(d["transcript_word"]) if d["transcript_word"] is not None else "—"
    if d["start"] is not None and d["end"] is not None:
        timing = f"{d['start']:.2f}s–{d['end']:.2f}s"
    else:
        timing = "—"
    return f"  [{d['miscue_type']:<16}] passage={passage:<30} heard={heard:<30} ({timing})"


def _run_one(
    passage_n: int,
    variant: str,
    classifier: MiscueClassifier,
    scorer: ScoringEngine,
    extractor: CapitalizationProperNounExtractor,
    show_correct: bool,
) -> None:
    """Classify + score one passage/variant pair and print the report."""
    text = _load_passage(passage_n)
    words = _load_transcript(passage_n, variant)
    total = _passage_word_count(text)
    proper_nouns = extractor.extract(text)

    details = classifier.detail(words, text, proper_nouns)
    counts = classifier.classify(words, text, proper_nouns)
    scoring = scorer.score(words, counts, total)

    print()
    print("=" * 80)
    print(f"Passage {passage_n} — {variant:<9}  ({total} passage words, {len(words)} transcript tokens)")
    print("=" * 80)
    print(f"Proper nouns detected: {proper_nouns or '—'}")

    print("\nCounts:")
    for key in ("correct", "mispronunciation", "substitution", "omission", "insertion", "repetition"):
        value = counts[key]  # type: ignore[literal-required]
        flag = "  (error)" if key in _ERROR_TYPES and value > 0 else ""
        print(f"  {key:<20} {value}{flag}")
    total_errors = sum(counts[k] for k in ("mispronunciation", "substitution", "omission", "insertion", "repetition"))  # type: ignore[literal-required]
    print(f"  {'TOTAL ERRORS':<20} {total_errors}")

    print("\nScoring:")
    print(f"  WPM:                {scoring['wpm']:.1f}")
    print(f"  Word recognition %: {scoring['word_recognition_pct']:.1f}")
    print(f"  Reading level:      {scoring['reading_level']}")

    events = details if show_correct else [d for d in details if d["miscue_type"] != "correct"]
    if not events:
        print("\nNo miscue events." if not show_correct else "\nNo events to display.")
        return
    label = "Events" if show_correct else "Miscue events"
    print(f"\n{label} ({len(events)}):")
    for d in events:
        print(_format_detail(d))


def main() -> int:
    """CLI entrypoint. Returns 0 on success, 2 if a passage/variant CSV is missing."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--passage",
        type=int,
        choices=range(1, 8),
        metavar="N",
        help="Single passage 1–7 (default: all 7)",
    )
    parser.add_argument(
        "--variant",
        choices=["correct", "incorrect", "both"],
        default="both",
        help="Which reader variant to inspect (default: both)",
    )
    parser.add_argument(
        "--show-correct",
        action="store_true",
        help="Also print 'correct' events (default: miscues only)",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level — INFO+ surfaces classifier diagnostics (default: WARNING)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format="%(name)s - %(levelname)s - %(message)s")

    passages = [args.passage] if args.passage else list(range(1, 8))
    variants = ["correct", "incorrect"] if args.variant == "both" else [args.variant]

    classifier = MiscueClassifier()
    scorer = ScoringEngine()
    extractor = CapitalizationProperNounExtractor()

    for n in passages:
        for v in variants:
            csv_path = _TRANSCRIPT_DIR / f"passage{n}{v}.transcription.csv"
            if not csv_path.exists():
                print(f"missing transcription CSV: {csv_path}", file=sys.stderr)
                return 2
            _run_one(n, v, classifier, scorer, extractor, show_correct=args.show_correct)
    return 0


if __name__ == "__main__":
    sys.exit(main())
