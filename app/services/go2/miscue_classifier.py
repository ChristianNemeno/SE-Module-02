import re
from collections import Counter
from difflib import SequenceMatcher

from app.models.miscue import MiscueCounts, MiscueDetail, MiscueType
from app.models.transcription import WordSegment

_REFUSAL_SCORE_THRESHOLD = 0.3
_MISPRONUNCIATION_MAX_DIST = 3


def _levenshtein(a: str, b: str) -> int:
    """Character-level edit distance (insert / delete / substitute)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[j] = min(dp[j - 1] + 1, dp[j] + 1, prev + cost)
            prev = temp
    return dp[n]


class MiscueClassifier:
    """Rule-based Phil-IRI miscue classifier. Maps aligned transcript to 7 categories."""

    def classify(
        self,
        transcript_words: list[WordSegment],
        passage_text: str,
        proper_nouns: list[str] | None = None,
    ) -> MiscueCounts:
        """Aligns transcript to passage and returns per-category miscue counts."""
        tally: Counter[MiscueType] = Counter(
            d["miscue_type"]
            for d in self._align(transcript_words, passage_text, proper_nouns)
        )
        return MiscueCounts(
            correct=tally["correct"],
            mispronunciation=tally["mispronunciation"],
            substitution=tally["substitution"],
            omission=tally["omission"],
            insertion=tally["insertion"],
            repetition=tally["repetition"],
            refusal_to_pronounce=tally["refusal_to_pronounce"],
        )

    def detail(
        self,
        transcript_words: list[WordSegment],
        passage_text: str,
        proper_nouns: list[str] | None = None,
    ) -> list[MiscueDetail]:
        """Aligns transcript to passage and returns one detail record per word decision."""
        return self._align(transcript_words, passage_text, proper_nouns)

    def _align(
        self,
        transcript_words: list[WordSegment],
        passage_text: str,
        proper_nouns: list[str] | None,
    ) -> list[MiscueDetail]:
        """Single source of truth — aligns passage to transcript into per-word detail records."""
        passage_tokens = self._tokenize(passage_text)
        proper_set = {w.lower() for w in (proper_nouns or [])}
        rep_details, deduped = self._detect_repetitions(transcript_words)
        deduped_tokens = [w["word"] for w in deduped]

        details: list[MiscueDetail] = []
        matcher = SequenceMatcher(None, passage_tokens, deduped_tokens, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    details.append(self._spoken("correct", passage_tokens[i1 + k], deduped[j1 + k]))
            elif tag == "replace":
                details.extend(
                    self._align_replace(passage_tokens[i1:i2], deduped[j1:j2], proper_set)
                )
            elif tag == "delete":
                for k in range(i1, i2):
                    details.append(self._omission(passage_tokens[k]))
            elif tag == "insert":
                for k in range(j1, j2):
                    details.append(self._insertion(deduped[k]))

        details.extend(rep_details)
        return details

    def _align_replace(
        self, p_words: list[str], t_segments: list[WordSegment], proper_set: set[str]
    ) -> list[MiscueDetail]:
        """Pairs replaced words 1-to-1; leftover passage/transcript words become omission/insertion."""
        out: list[MiscueDetail] = []
        pair_count = min(len(p_words), len(t_segments))
        for k in range(pair_count):
            seg = t_segments[k]
            label = self._classify_replace(p_words[k], seg["word"], seg["score"], proper_set)
            out.append(self._spoken(label, p_words[k], seg))
        for k in range(pair_count, len(p_words)):
            out.append(self._omission(p_words[k]))
        for k in range(pair_count, len(t_segments)):
            out.append(self._insertion(t_segments[k]))
        return out

    def _classify_replace(
        self, passage_word: str, transcript_word: str, score: float, proper_set: set[str]
    ) -> MiscueType:
        """Labels one word mismatch. Proper nouns read aloud count correct; conservative otherwise."""
        if score < _REFUSAL_SCORE_THRESHOLD:
            return "refusal_to_pronounce"
        if passage_word in proper_set:
            return "correct"  # ASR can't reliably spell names — don't penalize on edit distance
        dist = _levenshtein(passage_word, transcript_word)
        if dist <= 1:
            return "correct"
        if dist <= _MISPRONUNCIATION_MAX_DIST:
            return "mispronunciation"
        return "substitution"

    def _detect_repetitions(
        self, words: list[WordSegment]
    ) -> tuple[list[MiscueDetail], list[WordSegment]]:
        """Splits out consecutive duplicate words as repetition details; returns (reps, deduped)."""
        if not words:
            return [], []
        rep_details: list[MiscueDetail] = []
        deduped: list[WordSegment] = [words[0]]
        for i in range(1, len(words)):
            if words[i]["word"] == words[i - 1]["word"]:
                rep_details.append(
                    MiscueDetail(
                        miscue_type="repetition",
                        passage_word=None,
                        transcript_word=words[i]["word"],
                        start=words[i]["start"],
                        end=words[i]["end"],
                    )
                )
            else:
                deduped.append(words[i])
        return rep_details, deduped

    def _spoken(
        self, miscue_type: MiscueType, passage_word: str, seg: WordSegment
    ) -> MiscueDetail:
        """Builds a detail for a passage word that was actually spoken (carries timing)."""
        return MiscueDetail(
            miscue_type=miscue_type,
            passage_word=passage_word,
            transcript_word=seg["word"],
            start=seg["start"],
            end=seg["end"],
        )

    def _omission(self, passage_word: str) -> MiscueDetail:
        """Builds an omission detail — passage word with no spoken counterpart."""
        return MiscueDetail(
            miscue_type="omission",
            passage_word=passage_word,
            transcript_word=None,
            start=None,
            end=None,
        )

    def _insertion(self, seg: WordSegment) -> MiscueDetail:
        """Builds an insertion detail — spoken word with no passage counterpart."""
        return MiscueDetail(
            miscue_type="insertion",
            passage_word=None,
            transcript_word=seg["word"],
            start=seg["start"],
            end=seg["end"],
        )

    def _tokenize(self, text: str) -> list[str]:
        """Lowercases and extracts word tokens, strips punctuation."""
        return [w.lower() for w in re.findall(r"[a-zA-Z']+", text)]
