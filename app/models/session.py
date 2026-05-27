from typing import Protocol, TypedDict


class SessionRecord(TypedDict):
    """Flat record written to Supabase sessions table after a pipeline run."""

    learner_id: str          # UUID string, or "" to skip the insert
    passage_id: str
    wpm: float
    word_recognition_pct: float
    reading_level: str
    correct: int
    mispronunciation: int
    substitution: int
    omission: int
    insertion: int
    repetition: int
    finger_pointing: bool
    loss_of_place: bool
    monotone_reading: bool
    word_by_word_reading: bool
    inaudible_reading: bool


class SessionRepositoryProtocol(Protocol):
    """Interface for writing a completed session to Supabase."""

    def insert(self, record: SessionRecord) -> None:
        """Persist the record. No-op if learner_id is blank. Raises on DB error."""
        ...
