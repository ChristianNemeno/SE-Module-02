from typing import Protocol, TypedDict


class PassageRecord(TypedDict):
    """Passage text and word count fetched from Supabase."""

    text: str
    word_count: int


class PassageRepositoryProtocol(Protocol):
    """Interface for fetching passage text by ID."""

    def fetch(self, passage_id: str) -> PassageRecord:
        """Return passage text and word count. Raises ValueError if not found."""
        ...
