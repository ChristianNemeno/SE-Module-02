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


def test_detail_mispronunciation_carries_words_and_timing(clf: MiscueClassifier) -> None:
    """detail() records passage word, heard word, and spoken timing for a mispronunciation."""
    passage = "friend"
    words = [WordSegment(word="freind", start=1.2, end=1.5, score=0.9)]
    details = clf.detail(words, passage)
    mispron = [d for d in details if d["miscue_type"] == "mispronunciation"]
    assert len(mispron) == 1
    assert mispron[0]["passage_word"] == "friend"
    assert mispron[0]["transcript_word"] == "freind"
    assert mispron[0]["start"] == 1.2
    assert mispron[0]["end"] == 1.5


def test_detail_omission_has_no_transcript_word_or_timing(clf: MiscueClassifier) -> None:
    """detail() omission record has the passage word but no heard word or timing."""
    passage = "the big cat"
    words = [_w("the"), _w("cat")]
    details = clf.detail(words, passage)
    omission = [d for d in details if d["miscue_type"] == "omission"]
    assert len(omission) == 1
    assert omission[0]["passage_word"] == "big"
    assert omission[0]["transcript_word"] is None
    assert omission[0]["start"] is None
    assert omission[0]["end"] is None


def test_proper_noun_read_counts_as_correct(clf: MiscueClassifier) -> None:
    """A spoken proper noun counts correct despite ASR mis-spelling; penalized without the list."""
    passage = "anansi the spider"
    words = [_w("nancy"), _w("the"), _w("spider")]
    lenient = clf.classify(words, passage, proper_nouns=["Anansi"])  # case-insensitive
    strict = clf.classify(words, passage)
    assert lenient["correct"] == 3
    assert lenient["mispronunciation"] == 0
    assert lenient["substitution"] == 0
    assert strict["correct"] == 2  # "nancy" is penalized when the name isn't whitelisted


def test_proper_noun_refusal_still_refusal(clf: MiscueClassifier) -> None:
    """Leniency doesn't rescue a refusal — score < 0.3 stays refusal even for a proper noun."""
    passage = "anansi"
    words = [_w("uh", score=0.1)]
    counts = clf.classify(words, passage, proper_nouns=["anansi"])
    assert counts["refusal_to_pronounce"] == 1
    assert counts["correct"] == 0


def test_proper_noun_omission_still_omission(clf: MiscueClassifier) -> None:
    """Leniency only applies to spoken words — a skipped proper noun is still an omission."""
    passage = "anansi the spider"
    words = [_w("the"), _w("spider")]
    counts = clf.classify(words, passage, proper_nouns=["anansi"])
    assert counts["omission"] == 1
    assert counts["correct"] == 2


def test_detail_types_match_classify_counts(clf: MiscueClassifier) -> None:
    """The detail list tallied by type equals the classify() counts (single source of truth)."""
    passage = "the big cat sat on the mat"
    words = [_w("the"), _w("the"), _w("cot"), _w("um"), _w("sat"), _w("on"), _w("the"), _w("mat")]
    counts = clf.classify(words, passage)
    details = clf.detail(words, passage)
    for category, expected in counts.items():
        assert sum(1 for d in details if d["miscue_type"] == category) == expected
