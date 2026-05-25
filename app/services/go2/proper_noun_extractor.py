import re

_SENTENCE_SPLIT = re.compile(r"[.!?]+")
_WORD = re.compile(r"[A-Za-z']+")
_STOPWORDS = frozenset({"i", "i'm", "i'll", "i've", "i'd"})  # capitalized but not proper nouns


class CapitalizationProperNounExtractor:
    """Derives a passage's proper nouns from capitalization — no curated DB list needed."""

    def extract(self, passage_text: str) -> list[str]:
        """Lowercased proper nouns: any word capitalized in a non-sentence-initial slot."""
        found: set[str] = set()
        for sentence in _SENTENCE_SPLIT.split(passage_text):
            words = _WORD.findall(sentence)
            for word in words[1:]:  # skip sentence-initial word — always capitalized
                if word[0].isupper():
                    found.add(word.lower())
        return sorted(found - _STOPWORDS)
