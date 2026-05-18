import pytest
from app.models.miscue import MiscueCounts
from app.models.transcription import WordSegment
from app.services.go2.scoring_engine import ScoringEngine


def _w(word: str, start: float, end: float, score: float = 0.9) -> WordSegment:
    return WordSegment(word=word, start=start, end=end, score=score)


def _zero_counts() -> MiscueCounts:
    return MiscueCounts(
        correct=0,
        mispronunciation=0,
        substitution=0,
        omission=0,
        insertion=0,
        repetition=0,
        refusal_to_pronounce=0,
    )


@pytest.fixture
def engine() -> ScoringEngine:
    return ScoringEngine()


def test_wpm_100_words_in_90_seconds(engine: ScoringEngine) -> None:
    """100 words read in 90s → 66.7 WPM (within 0.1)."""
    words = [_w("x", 0.0, 0.5), _w("y", 89.5, 90.0)]
    counts = _zero_counts()
    counts["correct"] = 100
    result = engine.score(words, counts, total_passage_words=100)
    assert result["wpm"] == pytest.approx(66.7, abs=0.1)


def test_3_errors_in_50_words_is_instructional(engine: ScoringEngine) -> None:
    """3 errors in 50 words → 94% → Instructional."""
    words = [_w("x", 0.0, 0.5), _w("y", 29.5, 30.0)]
    counts = _zero_counts()
    counts["correct"] = 47
    counts["mispronunciation"] = 2
    counts["substitution"] = 1
    result = engine.score(words, counts, total_passage_words=50)
    assert result["word_recognition_pct"] == pytest.approx(94.0, abs=0.01)
    assert result["reading_level"] == "Instructional"


def test_7_errors_in_50_words_is_frustration(engine: ScoringEngine) -> None:
    """7 errors in 50 words → 86% → Frustration."""
    words = [_w("x", 0.0, 0.5), _w("y", 29.5, 30.0)]
    counts = _zero_counts()
    counts["correct"] = 43
    counts["mispronunciation"] = 3
    counts["substitution"] = 2
    counts["omission"] = 1
    counts["refusal_to_pronounce"] = 1
    result = engine.score(words, counts, total_passage_words=50)
    assert result["word_recognition_pct"] == pytest.approx(86.0, abs=0.01)
    assert result["reading_level"] == "Frustration"


def test_0_errors_in_52_words_is_independent(engine: ScoringEngine) -> None:
    """0 errors in 52 words → 100% → Independent."""
    words = [_w("x", 0.0, 0.5), _w("y", 29.5, 30.0)]
    counts = _zero_counts()
    counts["correct"] = 52
    result = engine.score(words, counts, total_passage_words=52)
    assert result["word_recognition_pct"] == pytest.approx(100.0, abs=0.01)
    assert result["reading_level"] == "Independent"


def test_insertions_and_repetitions_are_not_errors(engine: ScoringEngine) -> None:
    """Per Phil-IRI: insertion and repetition do NOT lower word-recognition."""
    words = [_w("x", 0.0, 0.5), _w("y", 29.5, 30.0)]
    counts = _zero_counts()
    counts["correct"] = 50
    counts["insertion"] = 5
    counts["repetition"] = 5
    result = engine.score(words, counts, total_passage_words=50)
    assert result["word_recognition_pct"] == pytest.approx(100.0, abs=0.01)
    assert result["reading_level"] == "Independent"


def test_empty_transcript_returns_zero_wpm(engine: ScoringEngine) -> None:
    """Empty transcript (refusal of entire passage) → wpm=0, level=Frustration."""
    counts = _zero_counts()
    counts["omission"] = 10
    result = engine.score([], counts, total_passage_words=10)
    assert result["wpm"] == 0.0
    assert result["word_recognition_pct"] == pytest.approx(0.0, abs=0.01)
    assert result["reading_level"] == "Frustration"


def test_zero_passage_words_does_not_crash(engine: ScoringEngine) -> None:
    """Degenerate passage (no words) → all zeros, level=Frustration, no ZeroDivisionError."""
    result = engine.score([], _zero_counts(), total_passage_words=0)
    assert result["wpm"] == 0.0
    assert result["word_recognition_pct"] == 0.0
    assert result["reading_level"] == "Frustration"


def test_threshold_91_is_instructional(engine: ScoringEngine) -> None:
    """Exactly 91% → Instructional (boundary inclusive per CLAUDE.md formulas)."""
    words = [_w("x", 0.0, 0.5), _w("y", 29.5, 30.0)]
    counts = _zero_counts()
    counts["correct"] = 91
    counts["mispronunciation"] = 9
    result = engine.score(words, counts, total_passage_words=100)
    assert result["word_recognition_pct"] == pytest.approx(91.0, abs=0.01)
    assert result["reading_level"] == "Instructional"


def test_threshold_97_is_independent(engine: ScoringEngine) -> None:
    """Exactly 97% → Independent (boundary inclusive per CLAUDE.md formulas)."""
    words = [_w("x", 0.0, 0.5), _w("y", 29.5, 30.0)]
    counts = _zero_counts()
    counts["correct"] = 97
    counts["mispronunciation"] = 3
    result = engine.score(words, counts, total_passage_words=100)
    assert result["word_recognition_pct"] == pytest.approx(97.0, abs=0.01)
    assert result["reading_level"] == "Independent"
