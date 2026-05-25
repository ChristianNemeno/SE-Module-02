import pytest

from app.services.go2.proper_noun_extractor import CapitalizationProperNounExtractor


@pytest.fixture
def extractor() -> CapitalizationProperNounExtractor:
    return CapitalizationProperNounExtractor()


def test_detects_mid_sentence_capitalized_name(extractor: CapitalizationProperNounExtractor) -> None:
    """A word capitalized mid-sentence is returned, lowercased."""
    assert "anansi" in extractor.extract("The spider met Anansi today.")


def test_all_occurrences_qualified_even_sentence_initial(
    extractor: CapitalizationProperNounExtractor,
) -> None:
    """A name seen capitalized mid-sentence qualifies the word — covers sentence-initial uses too."""
    assert extractor.extract("Anansi climbed the tree. He met Anansi.") == ["anansi"]


def test_ignores_sentence_initial_only_words(
    extractor: CapitalizationProperNounExtractor,
) -> None:
    """A word only ever at sentence start (e.g. 'The') is not treated as a proper noun."""
    assert extractor.extract("The cat sat. The dog ran.") == []


def test_excludes_pronoun_i(extractor: CapitalizationProperNounExtractor) -> None:
    """'I' is capitalized mid-sentence but stoplisted; real names are still found."""
    result = extractor.extract("Then I saw Jackie run.")
    assert "i" not in result
    assert "jackie" in result


def test_empty_passage_returns_empty(extractor: CapitalizationProperNounExtractor) -> None:
    """No text → no proper nouns."""
    assert extractor.extract("") == []


def test_multiple_names_sorted_and_deduped(
    extractor: CapitalizationProperNounExtractor,
) -> None:
    """Distinct names returned sorted, no duplicates."""
    assert extractor.extract("First came Jackie. Then Anansi waved at Jackie again.") == [
        "anansi",
        "jackie",
    ]
