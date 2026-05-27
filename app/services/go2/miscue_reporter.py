from app.models.miscue import MiscueDetail


class MiscueReporter:
    """Prints per-miscue detail to the console after GO2 analysis. Diagnostic only."""

    def report(self, passage_id: str, details: list[MiscueDetail]) -> None:
        """Prints the full word-for-word breakdown — correct words and miscues, with timing."""
        miscue_count = sum(1 for d in details if d["miscue_type"] != "correct")
        print(f"=== Word breakdown for {passage_id} ({len(details)} words, {miscue_count} miscues) ===")
        for d in details:
            print(self._format(d))

    def _format(self, detail: MiscueDetail) -> str:
        """Builds one aligned line for a single miscue."""
        passage = self._word(detail["passage_word"])
        heard = self._word(detail["transcript_word"])
        timing = self._timing(detail["start"], detail["end"])
        return f"[{detail['miscue_type']:<20}] passage={passage:<14} heard={heard:<14} ({timing})"

    def _word(self, word: str | None) -> str:
        """Quotes a word, or em dash when absent (omission/insertion)."""
        return f"'{word}'" if word is not None else "—"

    def _timing(self, start: float | None, end: float | None) -> str:
        """Formats start–end seconds, or em dash when timing is absent."""
        if start is None or end is None:
            return "—"
        return f"{start:.2f}s–{end:.2f}s"
