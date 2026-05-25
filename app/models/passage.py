from typing import NotRequired, Protocol, TypedDict


class PassageRecord(TypedDict):
    """Passage text and word count fetched from Supabase."""

    text: str
    word_count: int
    proper_nouns: NotRequired[list[str]]  # names/honorifics exempt from ASR-spelling penalties


class PassageRepositoryProtocol(Protocol):
    """Interface for fetching passage text by ID."""

    def fetch(self, passage_id: str) -> PassageRecord:
        """Return passage text and word count. Raises ValueError if not found."""
        ...
