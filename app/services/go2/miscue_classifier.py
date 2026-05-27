import logging
import re
from collections import Counter
from difflib import SequenceMatcher

from app.models.miscue import MiscueCounts, MiscueDetail, MiscueType
from app.models.transcription import WordSegment

_MISPRONUNCIATION_MAX_DIST = 3
_COLLAPSE_DURATION_THRESHOLD = 0.6
_HONORIFIC_STEMS: frozenset[str] = frozenset({"mang", "aling", "ate", "kuya", "lola", "lolo"})
_INFLECTION_SUFFIXES: tuple[str, ...] = ("ing", "es", "ed", "s", "d")
_MAX_REPETITION_PHRASE_LEN = 3
_CANON_RE = re.compile(r"[a-z']+")

logger = logging.getLogger(__name__)


def _canon(word: str) -> str:
    """Canonical matching form — lowercase letters + apostrophes only, punctuation removed."""
    return "".join(_CANON_RE.findall(word.lower()))


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
    """Rule-based Phil-IRI miscue classifier — 5 categories, phrase-aware event counting."""

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
        )

    def detail(
        self,
        transcript_words: list[WordSegment],
        passage_text: str,
        proper_nouns: list[str] | None = None,
    ) -> list[MiscueDetail]:
        """Aligns transcript to passage and returns one event record per Phil-IRI miscue."""
        return self._align(transcript_words, passage_text, proper_nouns)

    def _align(
        self,
        transcript_words: list[WordSegment],
        passage_text: str,
        proper_nouns: list[str] | None,
    ) -> list[MiscueDetail]:
        """Single source of truth — aligns passage to transcript and yields event records."""
        passage_tokens = self._tokenize(passage_text)
        proper_set = {w.lower() for w in (proper_nouns or [])}
        normalized = self._normalize_honorifics(transcript_words, passage_tokens)
        rep_details, deduped = self._detect_repetitions(normalized)
        deduped_canons = [_canon(w["word"]) for w in deduped]

        details: list[MiscueDetail] = []
        matcher = SequenceMatcher(None, passage_tokens, deduped_canons, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    details.append(self._spoken("correct", passage_tokens[i1 + k], deduped[j1 + k]))
            elif tag == "replace":
                details.append(
                    self._replace_event(passage_tokens[i1:i2], deduped[j1:j2], proper_set)
                )
            elif tag == "delete":
                details.append(self._omission_event(passage_tokens[i1:i2]))
            elif tag == "insert":
                details.append(self._insertion_event(deduped[j1:j2]))

        details.extend(rep_details)
        return details

    def _replace_event(
        self,
        p_words: list[str],
        t_segments: list[WordSegment],
        proper_set: set[str],
    ) -> MiscueDetail:
        """Collapses a replace opcode into one event — 1↔1 may be correct/mispron, else substitution."""
        if len(p_words) == 1 and len(t_segments) == 1:
            seg = t_segments[0]
            label = self._classify_pair(p_words[0], seg["word"], proper_set)
            return self._spoken(label, p_words[0], seg)
        self._flag_likely_collapse(t_segments)
        return MiscueDetail(
            miscue_type="substitution",
            passage_word=" ".join(p_words),
            transcript_word=" ".join(s["word"] for s in t_segments),
            start=t_segments[0]["start"] if t_segments else None,
            end=t_segments[-1]["end"] if t_segments else None,
        )

    def _classify_pair(
        self, passage_word: str, transcript_word: str, proper_set: set[str]
    ) -> MiscueType:
        """Labels a single-word mismatch with proper-noun and inflection leniency."""
        canon = _canon(transcript_word)
        if passage_word in proper_set:
            return "correct"  # ASR can't reliably spell names — don't penalize on edit distance
        if self._is_inflection_variant(passage_word, canon):
            return "correct"  # L2 morphological reductions (-ed, -s, -ing) — not a true miscue
        dist = _levenshtein(passage_word, canon)
        if dist <= 1:
            return "correct"
        if dist <= _MISPRONUNCIATION_MAX_DIST:
            return "mispronunciation"
        return "substitution"

    def _is_inflection_variant(self, a: str, b: str) -> bool:
        """True if a/b differ only by a trailing inflection suffix on either side."""
        if a == b or not a or not b:
            return False
        longer, shorter = (a, b) if len(a) > len(b) else (b, a)
        if not longer.startswith(shorter):
            return False
        suffix = longer[len(shorter):]
        return suffix in _INFLECTION_SUFFIXES

    def _detect_repetitions(
        self, words: list[WordSegment]
    ) -> tuple[list[MiscueDetail], list[WordSegment]]:
        """Collapses consecutive repeated words or phrases into single repetition events."""
        rep_details: list[MiscueDetail] = []
        deduped: list[WordSegment] = []
        i = 0
        n = len(words)
        while i < n:
            phrase_len = self._longest_repeated_phrase(words, i)
            if phrase_len > 0:
                span = words[i : i + phrase_len]
                tail = words[i + 2 * phrase_len - 1]
                rep_details.append(
                    MiscueDetail(
                        miscue_type="repetition",
                        passage_word=None,
                        transcript_word=" ".join(s["word"] for s in span),
                        start=span[0]["start"],
                        end=tail["end"],
                    )
                )
                deduped.extend(span)  # keep one copy for alignment
                i += 2 * phrase_len
            else:
                deduped.append(words[i])
                i += 1
        return rep_details, deduped

    def _longest_repeated_phrase(self, words: list[WordSegment], i: int) -> int:
        """Returns the largest k (1..MAX) such that words[i:i+k] == words[i+k:i+2k], else 0.

        Comparison is on the canonical form so trailing punctuation can't hide a repetition.
        """
        n = len(words)
        for k in range(_MAX_REPETITION_PHRASE_LEN, 0, -1):
            if i + 2 * k > n:
                continue
            left = [_canon(w["word"]) for w in words[i : i + k]]
            right = [_canon(w["word"]) for w in words[i + k : i + 2 * k]]
            if left == right:
                return k
        return 0

    def _flag_likely_collapse(self, t_segments: list[WordSegment]) -> None:
        """Log-only diagnostic — long single tokens often signal an ASR multi-word collapse."""
        for seg in t_segments:
            duration = seg["end"] - seg["start"]
            if duration > _COLLAPSE_DURATION_THRESHOLD:
                logger.warning(
                    "Likely ASR collapse: token=%r duration=%.2fs at %.2f-%.2fs",
                    seg["word"],
                    duration,
                    seg["start"],
                    seg["end"],
                )

    def _normalize_honorifics(
        self, words: list[WordSegment], passage_tokens: list[str]
    ) -> list[WordSegment]:
        """Splits transcript tokens that fused a Filipino honorific stem with a name.

        Only splits when the trailing remainder also matches a passage token, so we don't
        damage real words that happen to start with a stem (e.g. 'kuya' as a standalone).
        """
        passage_set = set(passage_tokens)
        out: list[WordSegment] = []
        for seg in words:
            stem, remainder = self._split_honorific(_canon(seg["word"]), passage_set)
            if stem is None or remainder is None:
                out.append(seg)
                continue
            mid = self._split_timing(seg, len(stem), len(stem) + len(remainder))
            out.append(WordSegment(word=stem, start=seg["start"], end=mid, score=seg["score"]))
            out.append(WordSegment(word=remainder, start=mid, end=seg["end"], score=seg["score"]))
        return out

    def _split_honorific(
        self, canon_token: str, passage_set: set[str]
    ) -> tuple[str | None, str | None]:
        """Returns (stem, remainder) if the canonical token is an honorific fusion the passage expects."""
        for stem in _HONORIFIC_STEMS:
            if not canon_token.startswith(stem) or len(canon_token) <= len(stem):
                continue
            if stem not in passage_set:
                continue
            remainder = canon_token[len(stem):]
            if remainder in passage_set:
                return stem, remainder
        return None, None

    def _split_timing(self, seg: WordSegment, left_len: int, total_len: int) -> float:
        """Linear interpolation of the split point within the original token's duration."""
        if total_len <= 0:
            return seg["start"]
        ratio = left_len / total_len
        return seg["start"] + (seg["end"] - seg["start"]) * ratio

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

    def _omission_event(self, p_words: list[str]) -> MiscueDetail:
        """Collapses a contiguous omitted passage span into one event."""
        return MiscueDetail(
            miscue_type="omission",
            passage_word=" ".join(p_words),
            transcript_word=None,
            start=None,
            end=None,
        )

    def _insertion_event(self, t_segments: list[WordSegment]) -> MiscueDetail:
        """Collapses a contiguous inserted transcript span into one event."""
        return MiscueDetail(
            miscue_type="insertion",
            passage_word=None,
            transcript_word=" ".join(s["word"] for s in t_segments),
            start=t_segments[0]["start"] if t_segments else None,
            end=t_segments[-1]["end"] if t_segments else None,
        )

    def _tokenize(self, text: str) -> list[str]:
        """Lowercases and extracts word tokens, strips punctuation."""
        return [w.lower() for w in re.findall(r"[a-zA-Z']+", text)]
