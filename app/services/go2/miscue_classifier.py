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
_TRANSCRIPT_MERGE_MAX_DIST = 1
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
        passage_canons, passage_displays, compound_set = self._merge_passage_compounds(
            passage_tokens, proper_set
        )
        normalized = self._merge_transcript_compounds(transcript_words, compound_set)
        rep_details, deduped = self._detect_repetitions(normalized)
        deduped_canons = [_canon(w["word"]) for w in deduped]

        details: list[MiscueDetail] = []
        matcher = SequenceMatcher(None, passage_canons, deduped_canons, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    details.append(
                        self._spoken("correct", passage_displays[i1 + k], deduped[j1 + k])
                    )
            elif tag == "replace":
                details.append(
                    self._replace_event(
                        passage_canons[i1:i2],
                        passage_displays[i1:i2],
                        deduped[j1:j2],
                        proper_set,
                        compound_set,
                    )
                )
            elif tag == "delete":
                details.append(self._omission_event(passage_displays[i1:i2]))
            elif tag == "insert":
                details.append(self._insertion_event(deduped[j1:j2]))

        details.extend(rep_details)
        return details

    def _replace_event(
        self,
        p_canons: list[str],
        p_displays: list[str],
        t_segments: list[WordSegment],
        proper_set: set[str],
        compound_set: set[str],
    ) -> MiscueDetail:
        """Collapses a replace opcode into one event — 1↔1 may be correct/mispron, else substitution."""
        if len(p_canons) == 1 and len(t_segments) == 1:
            seg = t_segments[0]
            is_compound = p_canons[0] in compound_set
            label = self._classify_pair(p_canons[0], seg["word"], proper_set, is_compound)
            return self._spoken(label, p_displays[0], seg)
        self._flag_likely_collapse(t_segments)
        return MiscueDetail(
            miscue_type="substitution",
            passage_word=" ".join(p_displays),
            transcript_word=" ".join(s["word"] for s in t_segments),
            start=t_segments[0]["start"] if t_segments else None,
            end=t_segments[-1]["end"] if t_segments else None,
        )

    def _classify_pair(
        self,
        passage_canon: str,
        transcript_word: str,
        proper_set: set[str],
        is_compound: bool,
    ) -> MiscueType:
        """Labels a single-word mismatch with proper-noun, compound, and inflection leniency."""
        canon = _canon(transcript_word)
        if passage_canon in proper_set or is_compound:
            return "correct"  # ASR can't reliably spell names; compounds carry one — don't penalize.
        if self._is_inflection_variant(passage_canon, canon):
            return "correct"  # L2 morphological reductions (-ed, -s, -ing) — not a true miscue.
        dist = _levenshtein(passage_canon, canon)
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

    def _merge_passage_compounds(
        self, passage_tokens: list[str], proper_set: set[str]
    ) -> tuple[list[str], list[str], set[str]]:
        """Merge Filipino honorific+name pairs in the passage into one canonical token.

        Returns (canons, displays, compound_canons): canons feed SequenceMatcher, displays
        carry the original space-separated form for MiscueDetail output, compound_canons
        lists the merged forms so the transcript-side merge knows what to look for.
        """
        canons: list[str] = []
        displays: list[str] = []
        compound_canons: set[str] = set()
        i = 0
        n = len(passage_tokens)
        while i < n:
            tok = passage_tokens[i]
            if i + 1 < n and tok in _HONORIFIC_STEMS and passage_tokens[i + 1] in proper_set:
                merged_canon = tok + passage_tokens[i + 1]
                canons.append(merged_canon)
                displays.append(f"{tok} {passage_tokens[i + 1]}")
                compound_canons.add(merged_canon)
                i += 2
            else:
                canons.append(tok)
                displays.append(tok)
                i += 1
        return canons, displays, compound_canons

    def _merge_transcript_compounds(
        self, words: list[WordSegment], compound_canons: set[str]
    ) -> list[WordSegment]:
        """Fuse consecutive transcript tokens whose joined canon closely matches a compound.

        Strict edit-distance threshold (≤ 1) — only rescues the case where the ASR cleanly
        emitted the honorific and name as two separate tokens. Genuine reader stumbles
        (joined canon farther from any compound) stay as two tokens so the 1↔2 replace
        opcode falls through to the span-substitution rule.
        """
        if not compound_canons:
            return list(words)
        out: list[WordSegment] = []
        i = 0
        n = len(words)
        while i < n:
            if i + 1 < n:
                joined = _canon(words[i]["word"]) + _canon(words[i + 1]["word"])
                if self._matches_any_compound(joined, compound_canons):
                    a, b = words[i], words[i + 1]
                    out.append(
                        WordSegment(
                            word=f"{a['word']} {b['word']}",
                            start=a["start"],
                            end=b["end"],
                            score=min(a["score"], b["score"]),
                        )
                    )
                    i += 2
                    continue
            out.append(words[i])
            i += 1
        return out

    def _matches_any_compound(self, joined_canon: str, compound_canons: set[str]) -> bool:
        """True if joined_canon is within the strict merge threshold of any compound."""
        if joined_canon in compound_canons:
            return True
        for c in compound_canons:
            if _levenshtein(joined_canon, c) <= _TRANSCRIPT_MERGE_MAX_DIST:
                return True
        return False

    def _spoken(
        self, miscue_type: MiscueType, passage_display: str, seg: WordSegment
    ) -> MiscueDetail:
        """Builds a detail for a passage word (or compound) that was actually spoken."""
        return MiscueDetail(
            miscue_type=miscue_type,
            passage_word=passage_display,
            transcript_word=seg["word"],
            start=seg["start"],
            end=seg["end"],
        )

    def _omission_event(self, p_displays: list[str]) -> MiscueDetail:
        """Collapses a contiguous omitted passage span into one event."""
        return MiscueDetail(
            miscue_type="omission",
            passage_word=" ".join(p_displays),
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
        """Lowercases and extracts word tokens, strips punctuation.

        Normalizes curly apostrophes (U+2019) to ASCII so possessives like 'Juaning's'
        survive as one token rather than splitting into ['juaning', 's'].
        """
        normalized = text.replace("’", "'")
        return [w.lower() for w in re.findall(r"[a-zA-Z']+", normalized)]
