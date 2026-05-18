import pytest
from app.models.transcription import WordSegment
from app.services.go2.miscue_classifier import MiscueClassifier


def _w(word: str, score: float = 0.9) -> WordSegment:
    return WordSegment(word=word, start=0.0, end=1.0, score=score)


@pytest.fixture
def clf() -> MiscueClassifier:
    return MiscueClassifier()


def test_perfect_read(clf: MiscueClassifier) -> None:
    """100% correct read — all 6 words correct, all others zero."""
    passage = "the cat sat on the mat"
    words = [_w(w) for w in ["the", "cat", "sat", "on", "the", "mat"]]
    counts = clf.classify(words, passage)
    assert counts["correct"] == 6
    assert counts["mispronunciation"] == 0
    assert counts["substitution"] == 0
    assert counts["omission"] == 0
    assert counts["insertion"] == 0
    assert counts["repetition"] == 0
    assert counts["refusal_to_pronounce"] == 0


def test_substitution(clf: MiscueClassifier) -> None:
    """'mountain' for 'cat' — edit distance > 3 → substitution."""
    passage = "the cat"
    words = [_w("the"), _w("mountain")]
    counts = clf.classify(words, passage)
    assert counts["substitution"] == 1
    assert counts["correct"] == 1


def test_omission(clf: MiscueClassifier) -> None:
    """Passage word 'big' absent in transcript → omission."""
    passage = "the big cat"
    words = [_w("the"), _w("cat")]
    counts = clf.classify(words, passage)
    assert counts["omission"] == 1
    assert counts["correct"] == 2


def test_insertion(clf: MiscueClassifier) -> None:
    """Extra word 'big' not in passage → insertion."""
    passage = "the cat"
    words = [_w("the"), _w("big"), _w("cat")]
    counts = clf.classify(words, passage)
    assert counts["insertion"] == 1
    assert counts["correct"] == 2


def test_empty_transcript(clf: MiscueClassifier) -> None:
    """Empty transcript → all 3 passage words become omissions."""
    passage = "the cat sat"
    counts = clf.classify([], passage)
    assert counts["omission"] == 3
    assert counts["correct"] == 0
    assert counts["insertion"] == 0
    assert counts["repetition"] == 0


def test_repetition(clf: MiscueClassifier) -> None:
    """'the the cat' — consecutive duplicate → repetition=1, deduped then aligned."""
    passage = "the cat"
    words = [_w("the"), _w("the"), _w("cat")]
    counts = clf.classify(words, passage)
    assert counts["repetition"] == 1
    assert counts["correct"] == 2


def test_mispronunciation(clf: MiscueClassifier) -> None:
    """'freind' for 'friend' — edit distance 2 → mispronunciation."""
    passage = "friend"
    words = [_w("freind")]
    counts = clf.classify(words, passage)
    assert counts["mispronunciation"] == 1


def test_refusal_to_pronounce(clf: MiscueClassifier) -> None:
    """Score < 0.3 → refusal_to_pronounce regardless of edit distance."""
    passage = "cat"
    words = [_w("kat", score=0.2)]
    counts = clf.classify(words, passage)
    assert counts["refusal_to_pronounce"] == 1


def test_all_seven_keys_always_present(clf: MiscueClassifier) -> None:
    """classify() always returns all 7 categories even when count is 0."""
    counts = clf.classify([], "word")
    expected = {
        "correct", "mispronunciation", "substitution",
        "omission", "insertion", "repetition", "refusal_to_pronounce",
    }
    assert set(counts.keys()) == expected
