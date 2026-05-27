from postgrest.exceptions import APIError
from supabase import Client

from app.models.passage import PassageRecord


class PassageRepository:
    """Fetches passage text and word count from the Supabase passages table."""

    def __init__(self, client: Client) -> None:
        """Store the Supabase client."""
        self._client = client

    def fetch(self, passage_id: str) -> PassageRecord:
        """Query passages by ID. Raises ValueError if the passage doesn't exist."""
        try:
            response = (
                self._client.table("passages")
                .select("text, word_count")
                .eq("id", passage_id)
                .single()
                .execute()
            )
        except APIError as exc:
            raise ValueError(f"Passage not found: {passage_id}") from exc

        data: dict[str, object] = response.data  # type: ignore[assignment]
        return PassageRecord(
            text=str(data["text"]),
            word_count=int(data["word_count"]),  # type: ignore[arg-type]
            # TODO: once the passages table has a `proper_nouns text[]` column, add it to the
            # select() above and map it here so the classifier can exempt names from penalties.
            proper_nouns=[],
        )
