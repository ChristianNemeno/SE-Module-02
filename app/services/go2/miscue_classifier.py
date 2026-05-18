import re
from difflib import SequenceMatcher

from app.models.miscue import MiscueCounts, MiscueType
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

    def classify(self, transcript_words: list[WordSegment], passage_text: str) -> MiscueCounts:
        """Aligns transcript to passage and returns per-category miscue counts."""
        passage_tokens = self._tokenize(passage_text)
        transcript_tokens = [w["word"] for w in transcript_words]
        transcript_scores = [w["score"] for w in transcript_words]

        rep_count, deduped_tokens, deduped_scores = self._detect_repetitions(
            transcript_tokens, transcript_scores
        )

        tally: dict[str, int] = {
            "correct": 0,
            "mispronunciation": 0,
            "substitution": 0,
            "omission": 0,
            "insertion": 0,
            "repetition": rep_count,
            "refusal_to_pronounce": 0,
        }

        matcher = SequenceMatcher(None, passage_tokens, deduped_tokens, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                tally["correct"] += i2 - i1
            elif tag == "replace":
                self._apply_replace(
                    passage_tokens[i1:i2],
                    deduped_tokens[j1:j2],
                    deduped_scores[j1:j2],
                    tally,
                )
            elif tag == "delete":
                tally["omission"] += i2 - i1
            elif tag == "insert":
                tally["insertion"] += j2 - j1

        return MiscueCounts(
            correct=tally["correct"],
            mispronunciation=tally["mispronunciation"],
            substitution=tally["substitution"],
            omission=tally["omission"],
            insertion=tally["insertion"],
            repetition=tally["repetition"],
            refusal_to_pronounce=tally["refusal_to_pronounce"],
        )

    def _apply_replace(
        self,
        p_words: list[str],
        t_words: list[str],
        t_scores: list[float],
        tally: dict[str, int],
    ) -> None:
        """Handles a replace opcode: pairs words 1-to-1, leftovers become omission/insertion."""
        pair_count = min(len(p_words), len(t_words))
        for k in range(pair_count):
            label = self._classify_replace(p_words[k], t_words[k], t_scores[k])
            tally[label] += 1
        tally["omission"] += len(p_words) - pair_count
        tally["insertion"] += len(t_words) - pair_count

    def _classify_replace(
        self, passage_word: str, transcript_word: str, score: float
    ) -> MiscueType:
        """Labels one word mismatch. Conservative: mispronunciation preferred over substitution."""
        if score < _REFUSAL_SCORE_THRESHOLD:
            return "refusal_to_pronounce"
        dist = _levenshtein(passage_word, transcript_word)
        if dist <= 1:
            return "correct"
        if dist <= _MISPRONUNCIATION_MAX_DIST:
            return "mispronunciation"
        return "substitution"

    def _detect_repetitions(
        self, tokens: list[str], scores: list[float]
    ) -> tuple[int, list[str], list[float]]:
        """Counts consecutive duplicate transcript words; returns (count, deduped, scores)."""
        if not tokens:
            return 0, [], []
        count = 0
        deduped_t: list[str] = [tokens[0]]
        deduped_s: list[float] = [scores[0]]
        for i in range(1, len(tokens)):
            if tokens[i] == tokens[i - 1]:
                count += 1
            else:
                deduped_t.append(tokens[i])
                deduped_s.append(scores[i])
        return count, deduped_t, deduped_s

    def _tokenize(self, text: str) -> list[str]:
        """Lowercases and extracts word tokens, strips punctuation."""
        return [w.lower() for w in re.findall(r"[a-zA-Z']+", text)]
