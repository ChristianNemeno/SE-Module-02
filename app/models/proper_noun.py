from typing import Protocol


class ProperNounExtractorProtocol(Protocol):
    """Interface for deriving a passage's proper nouns — pipeline depends on this, not the concrete."""

    def extract(self, passage_text: str) -> list[str]:
        """Return proper nouns (lowercased) detected in the passage text."""
        ...
