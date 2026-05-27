import logging

import pytest

from app.models.transcription import WordSegment
from app.services.go2.miscue_classifier import MiscueClassifier


def _w(word: str, start: float = 0.0, end: float = 1.0, score: float = 0.9) -> WordSegment:
    return WordSegment(word=word, start=start, end=end, score=score)


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
    """Empty transcript → contiguous passage span becomes a single omission event."""
    passage = "the cat sat"
    counts = clf.classify([], passage)
    assert counts["omission"] == 1
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


def test_all_five_keys_always_present(clf: MiscueClassifier) -> None:
    """classify() always returns all categories even when count is 0 (no refusal_to_pronounce)."""
    counts = clf.classify([], "word")
    expected = {
        "correct", "mispronunciation", "substitution",
        "omission", "insertion", "repetition",
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


def test_proper_noun_omission_still_omission(clf: MiscueClassifier) -> None:
    """Leniency only applies to spoken words — a skipped proper noun is still an omission."""
    passage = "anansi the spider"
    words = [_w("the"), _w("spider")]
    counts = clf.classify(words, passage, proper_nouns=["anansi"])
    assert counts["omission"] == 1
    assert counts["correct"] == 2


def test_phrase_omission_collapses_to_one_event(clf: MiscueClassifier) -> None:
    """Contiguous omitted passage words form one omission event with the joined phrase."""
    passage = "once in the small hill"
    words = [_w("once"), _w("in"), _w("hill")]
    details = clf.detail(words, passage)
    omissions = [d for d in details if d["miscue_type"] == "omission"]
    assert len(omissions) == 1
    assert omissions[0]["passage_word"] == "the small"


def test_phrase_insertion_collapses_to_one_event(clf: MiscueClassifier) -> None:
    """Contiguous inserted transcript words form one insertion event with the joined phrase."""
    passage = "said mama"
    words = [_w("said"), _w("by", start=0.5, end=0.7), _w("there", start=0.7, end=0.9), _w("mama")]
    details = clf.detail(words, passage)
    insertions = [d for d in details if d["miscue_type"] == "insertion"]
    assert len(insertions) == 1
    assert insertions[0]["transcript_word"] == "by there"
    assert insertions[0]["start"] == 0.5
    assert insertions[0]["end"] == 0.9


def test_phrase_repetition_collapses_to_one_event(clf: MiscueClassifier) -> None:
    """A repeated bigram like 'the cat the cat' counts as one repetition event."""
    passage = "the cat sat"
    words = [
        _w("the", start=0.0, end=0.2),
        _w("cat", start=0.2, end=0.5),
        _w("the", start=0.5, end=0.7),
        _w("cat", start=0.7, end=1.0),
        _w("sat", start=1.0, end=1.3),
    ]
    details = clf.detail(words, passage)
    reps = [d for d in details if d["miscue_type"] == "repetition"]
    assert len(reps) == 1
    assert reps[0]["transcript_word"] == "the cat"
    assert reps[0]["start"] == 0.0
    assert reps[0]["end"] == 1.0


def test_word_repetition_remains_one_event(clf: MiscueClassifier) -> None:
    """A single-word doubling like 'man man' still counts as one repetition."""
    passage = "a man shouted"
    words = [_w("a"), _w("man"), _w("man"), _w("shouted")]
    counts = clf.classify(words, passage)
    assert counts["repetition"] == 1
    assert counts["correct"] == 3


def test_span_substitution_is_one_event(clf: MiscueClassifier) -> None:
    """A 1-passage-word → N-transcript-token replacement counts as one substitution event."""
    passage = "the mouse got out"
    words = [
        _w("the", start=0.0, end=0.2),
        _w("mouse", start=0.2, end=0.5),
        _w("did", start=0.5, end=0.7),
        _w("not", start=0.7, end=0.9),
        _w("get", start=0.9, end=1.1),
        _w("out", start=1.1, end=1.3),
    ]
    details = clf.detail(words, passage)
    subs = [d for d in details if d["miscue_type"] == "substitution"]
    assert len(subs) == 1
    assert subs[0]["passage_word"] == "got"
    assert subs[0]["transcript_word"] == "did not get"


def test_inflection_tolerance_treats_dropped_ed_as_correct(clf: MiscueClassifier) -> None:
    """L2 dropped -ed inflection ('asked' → 'ask') is not a miscue."""
    passage = "she asked nicely"
    words = [_w("she"), _w("ask"), _w("nicely")]
    counts = clf.classify(words, passage)
    assert counts["correct"] == 3
    assert counts["mispronunciation"] == 0
    assert counts["substitution"] == 0


def test_inflection_tolerance_treats_dropped_s_as_correct(clf: MiscueClassifier) -> None:
    """Third-person -s drop ('says' → 'say') is not a miscue."""
    passage = "he says hi"
    words = [_w("he"), _w("say"), _w("hi")]
    counts = clf.classify(words, passage)
    assert counts["correct"] == 3
    assert counts["mispronunciation"] == 0


def test_honorific_normalization_recovers_alignment(clf: MiscueClassifier) -> None:
    """Filipino honorific+name ASR fusion ('mang ador' → 'mangador') aligns correctly.

    The passage compound 'Mang Ador' is treated as one unit, so counts.correct
    reflects 3 events (one for the compound, plus 'said' and 'hi').
    """
    passage = "Mang Ador said hi"
    words = [_w("mangador", start=0.0, end=0.6), _w("said"), _w("hi")]
    counts = clf.classify(words, passage, proper_nouns=["Ador"])
    assert counts["correct"] == 3
    assert counts["substitution"] == 0
    assert counts["mispronunciation"] == 0


def test_duration_flag_logs_but_does_not_change_class(
    clf: MiscueClassifier, caplog: pytest.LogCaptureFixture
) -> None:
    """A long transcript token in a substitution emits a warning but the classification is unchanged."""
    passage = "the cat sat"
    words = [
        _w("the"),
        _w("xylophonemaster", start=1.0, end=2.6),  # 1.6s — well above 0.6s threshold
        _w("zebrafish", start=2.6, end=4.0),
        _w("sat"),
    ]
    with caplog.at_level(logging.WARNING, logger="app.services.go2.miscue_classifier"):
        counts = clf.classify(words, passage)
    assert counts["substitution"] == 1
    assert any("Likely ASR collapse" in r.message for r in caplog.records)


def test_compound_fused_transcript_is_correct(clf: MiscueClassifier) -> None:
    """ASR fused 'Mang Tinoy's' → 'mangtinoys' aligns to the compound and reports correct."""
    passage = "Mang Tinoy's house"
    words = [_w("mangtinoys", start=0.0, end=0.6), _w("house")]
    counts = clf.classify(words, passage, proper_nouns=["Tinoy's"])
    assert counts["correct"] == 2
    assert counts["substitution"] == 0
    assert counts["mispronunciation"] == 0


def test_compound_phonetically_drifted_transcript_is_correct(clf: MiscueClassifier) -> None:
    """ASR phonetic drift on a name ('alingjuaning's' → 'alingwanning's') stays correct.

    Same proper-noun-leniency policy as 'anansi → nancy' — names are unreliable in ASR,
    don't penalize the reader for what the model misspells.
    """
    passage = "Aling Juaning's stall"
    words = [_w("alingwanning's", start=0.0, end=0.7), _w("stall")]
    counts = clf.classify(words, passage, proper_nouns=["Juaning's"])
    assert counts["correct"] == 2
    assert counts["substitution"] == 0
    assert counts["mispronunciation"] == 0


def test_compound_already_split_clean_transcript_is_correct(clf: MiscueClassifier) -> None:
    """When ASR emits the honorific and name as two clean tokens, they fuse into one event."""
    passage = "Mang Ador said hi"
    words = [
        _w("mang", start=0.0, end=0.2),
        _w("ador", start=0.2, end=0.5),
        _w("said"),
        _w("hi"),
    ]
    counts = clf.classify(words, passage, proper_nouns=["Ador"])
    assert counts["correct"] == 3
    assert counts["substitution"] == 0
    assert counts["mispronunciation"] == 0


def test_compound_two_token_stumble_is_substitution(clf: MiscueClassifier) -> None:
    """Reader stumble ('mangti' + 'noise' for 'Mang Tinoy's') stays as a single substitution event."""
    passage = "Mang Tinoy's house"
    words = [
        _w("mangti", start=0.0, end=0.3),
        _w("noise", start=0.3, end=0.6),
        _w("house"),
    ]
    details = clf.detail(words, passage, proper_nouns=["Tinoy's"])
    subs = [d for d in details if d["miscue_type"] == "substitution"]
    assert len(subs) == 1
    assert subs[0]["passage_word"] == "mang tinoy's"
    assert subs[0]["transcript_word"] == "mangti noise"


def test_compound_passage_word_uses_space_separated_display(clf: MiscueClassifier) -> None:
    """MiscueDetail.passage_word reports the original space form for compounds, not the merged canon."""
    passage = "Mang Ador said hi"
    words = [_w("mangador", start=0.0, end=0.5), _w("said"), _w("hi")]
    details = clf.detail(words, passage, proper_nouns=["Ador"])
    compound_events = [d for d in details if d["passage_word"] == "mang ador"]
    assert len(compound_events) == 1
    assert compound_events[0]["miscue_type"] == "correct"
    assert "mangador" not in [d["passage_word"] for d in details]


def test_compound_merge_requires_proper_noun_next(clf: MiscueClassifier) -> None:
    """A honorific stem followed by a non-proper-noun word stays unmerged (e.g. 'kuya ate breakfast')."""
    passage = "Kuya ate breakfast"  # 'ate' is the verb, not a name
    words = [_w("kuya"), _w("ate"), _w("breakfast")]
    counts = clf.classify(words, passage, proper_nouns=[])
    assert counts["correct"] == 3
    assert counts["substitution"] == 0


def test_transcript_punctuation_does_not_block_correct_match(clf: MiscueClassifier) -> None:
    """WhisperX-style trailing punctuation ('cat.') must still match the passage word 'cat'."""
    passage = "the cat sat"
    words = [_w("the,"), _w("cat."), _w("sat!")]
    counts = clf.classify(words, passage)
    assert counts["correct"] == 3
    assert counts["substitution"] == 0
    assert counts["mispronunciation"] == 0


def test_repetition_robust_to_punctuation(clf: MiscueClassifier) -> None:
    """Repetition detection compares canonical forms so 'the,' followed by 'the' still collapses."""
    passage = "the cat"
    words = [_w("the,"), _w("the"), _w("cat")]
    counts = clf.classify(words, passage)
    assert counts["repetition"] == 1
    assert counts["correct"] == 2


def test_detail_keeps_raw_transcript_word_with_punctuation(clf: MiscueClassifier) -> None:
    """A matched event preserves the raw ASR token in MiscueDetail (display-friendly)."""
    passage = "bed"
    words = [_w("bed.")]
    details = clf.detail(words, passage)
    assert len(details) == 1
    assert details[0]["miscue_type"] == "correct"
    assert details[0]["transcript_word"] == "bed."  # raw token retained for display
    assert details[0]["passage_word"] == "bed"


def test_honorific_normalization_handles_punctuation(clf: MiscueClassifier) -> None:
    """Honorific fusion + trailing punctuation ('mangador,') aligns to the compound."""
    passage = "Mang Ador said hi"
    words = [_w("mangador,", start=0.0, end=0.6), _w("said"), _w("hi")]
    counts = clf.classify(words, passage, proper_nouns=["Ador"])
    assert counts["correct"] == 3
    assert counts["substitution"] == 0
    assert counts["mispronunciation"] == 0


def test_detail_types_match_classify_counts(clf: MiscueClassifier) -> None:
    """The detail list tallied by type equals the classify() counts (single source of truth)."""
    passage = "the big cat sat on the mat"
    words = [_w("the"), _w("the"), _w("cot"), _w("um"), _w("sat"), _w("on"), _w("the"), _w("mat")]
    counts = clf.classify(words, passage)
    details = clf.detail(words, passage)
    for category, expected in counts.items():
        assert sum(1 for d in details if d["miscue_type"] == category) == expected
