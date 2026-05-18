from app.models.assessment import ReadingLevel
from app.models.miscue import MiscueCounts
from app.models.scoring import ScoringResult
from app.models.transcription import WordSegment

_INDEPENDENT_MIN_PCT = 97.0
_INSTRUCTIONAL_MIN_PCT = 91.0


class ScoringEngine:
    """Computes Phil-IRI scoring fields (WPM, word-recognition %, reading level)."""

    def score(
        self,
        transcript_words: list[WordSegment],
        miscue_counts: MiscueCounts,
        total_passage_words: int,
    ) -> ScoringResult:
        """Builds the GO2 scoring result from miscue counts and word timings."""
        wpm = self._wpm(transcript_words, total_passage_words)
        pct = self._word_recognition_pct(miscue_counts, total_passage_words)
        level = self._reading_level(pct)
        return ScoringResult(wpm=wpm, word_recognition_pct=pct, reading_level=level)

    def _wpm(self, words: list[WordSegment], total_passage_words: int) -> float:
        """WPM uses passage word count over transcript-reading duration. 0 if no audio."""
        if not words or total_passage_words == 0:
            return 0.0
        duration = words[-1]["end"] - words[0]["start"]
        if duration <= 0:
            return 0.0
        return total_passage_words / duration * 60.0

    def _word_recognition_pct(self, counts: MiscueCounts, total: int) -> float:
        """Errors = mispron + sub + omission + refusal. NOT insertion or repetition."""
        if total == 0:
            return 0.0
        errors = (
            counts["mispronunciation"]
            + counts["substitution"]
            + counts["omission"]
            + counts["refusal_to_pronounce"]
        )
        return (total - errors) / total * 100.0

    def _reading_level(self, pct: float) -> ReadingLevel:
        """Phil-IRI thresholds: ≥97 Independent, ≥91 Instructional, else Frustration."""
        if pct >= _INDEPENDENT_MIN_PCT:
            return "Independent"
        if pct >= _INSTRUCTIONAL_MIN_PCT:
            return "Instructional"
        return "Frustration"
