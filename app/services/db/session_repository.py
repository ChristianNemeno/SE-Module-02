from supabase import Client

from app.models.session import SessionRecord


class SessionRepository:
    """Writes completed session records to the Supabase sessions table."""

    def __init__(self, client: Client) -> None:
        """Store the Supabase client."""
        self._client = client

    def insert(self, record: SessionRecord) -> None:
        """Insert the record. Skips if learner_id is blank. Raises on DB error."""
        if not record["learner_id"].strip():
            return
        self._client.table("sessions").insert(dict(record)).execute()  # type: ignore[arg-type]
