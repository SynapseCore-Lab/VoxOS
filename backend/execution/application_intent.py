from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum

from tools.system.application_model import Application
from tools.system.application_registry import ApplicationRegistry


class MatchConfidence(str, Enum):
    """
    Confidence category for an application match.
    """

    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class ApplicationMatch:
    """
    Result of resolving spoken text to an application.
    """

    application: Application
    score: float
    matched_text: str
    confidence: MatchConfidence


class ApplicationIntentResolver:
    """
    Resolves spoken application names against the
    discovered application registry.

    Matching strategy:

        1. Exact name / alias
        2. Compact similarity
        3. Token similarity
        4. Character n-gram similarity
        5. Word-boundary similarity
        6. Anchored token similarity
        7. Phonetic similarity
        8. Combined confidence score

    The resolver NEVER launches an application itself.

    Confidence policy:

        EXACT
            Exact registry match.

        HIGH
            Strong fuzzy match.

        MEDIUM
            Possible match requiring confirmation.

        LOW
            Insufficient confidence.
    """

    ACTION_WORDS = {
        "open",
        "launch",
        "start",
        "run",
    }

    HIGH_CONFIDENCE_SCORE = 0.78
    MEDIUM_CONFIDENCE_SCORE = 0.55

    def __init__(
        self,
        registry: ApplicationRegistry,
    ) -> None:
        self.registry = registry

    # =========================================================
    # PUBLIC API
    # =========================================================

    def resolve(
        self,
        text: str,
    ) -> ApplicationMatch | None:
        """
        Resolve spoken text to an installed application.

        Returns None when confidence is too low.
        """

        normalized = self._normalize(text)

        if not normalized:
            return None

        command = self._remove_action_prefix(normalized)

        if not command:
            return None

        # -----------------------------------------------------
        # Exact lookup
        # -----------------------------------------------------

        exact = self.registry.get(command)

        if exact is not None:
            return ApplicationMatch(
                application=exact,
                score=1.0,
                matched_text=command,
                confidence=MatchConfidence.EXACT,
            )

        # -----------------------------------------------------
        # Find best fuzzy candidate.
        # -----------------------------------------------------

        best = self._find_best_candidate(command)

        if best is None:
            return None

        # -----------------------------------------------------
        # LOW confidence is rejected.
        # -----------------------------------------------------

        if best.score < self.MEDIUM_CONFIDENCE_SCORE:
            return None

        return ApplicationMatch(
            application=best.application,
            score=best.score,
            matched_text=best.matched_text,
            confidence=self._confidence_from_score(
                best.score
            ),
        )

    # =========================================================
    # CANDIDATE SEARCH
    # =========================================================

    def _find_best_candidate(
        self,
        command: str,
    ) -> ApplicationMatch | None:
        """
        Search the application registry and return the
        highest-scoring candidate.

        This internal method allows medium-confidence matches
        to be returned for confirmation.
        """

        best: ApplicationMatch | None = None

        for application in self.registry.all():

            candidates = (
                application.name,
                *application.aliases,
            )

            for candidate in candidates:

                candidate_normalized = self._normalize(
                    candidate
                )

                if not candidate_normalized:
                    continue

                score = self._calculate_score(
                    command,
                    candidate_normalized,
                )

                confidence = self._confidence_from_score(
                    score
                )

                match = ApplicationMatch(
                    application=application,
                    score=score,
                    matched_text=candidate_normalized,
                    confidence=confidence,
                )

                if (
                    best is None
                    or match.score > best.score
                ):
                    best = match

        return best

    # =========================================================
    # CONFIDENCE
    # =========================================================

    @classmethod
    def _confidence_from_score(
        cls,
        score: float,
    ) -> MatchConfidence:
        """
        Convert numerical similarity into a confidence level.
        """

        if score >= 0.999:
            return MatchConfidence.EXACT

        if score >= cls.HIGH_CONFIDENCE_SCORE:
            return MatchConfidence.HIGH

        if score >= cls.MEDIUM_CONFIDENCE_SCORE:
            return MatchConfidence.MEDIUM

        return MatchConfidence.LOW

    # =========================================================
    # SCORING
    # =========================================================

    def _calculate_score(
        self,
        query: str,
        candidate: str,
    ) -> float:
        """
        Calculate a multi-signal speech-oriented score.
        """

        compact_query = self._compact(query)
        compact_candidate = self._compact(candidate)

        # -----------------------------------------------------
        # Signal 1: Normal string similarity
        # -----------------------------------------------------

        sequence_score = SequenceMatcher(
            None,
            query,
            candidate,
        ).ratio()

        # -----------------------------------------------------
        # Signal 2: Compact similarity
        # -----------------------------------------------------

        compact_score = SequenceMatcher(
            None,
            compact_query,
            compact_candidate,
        ).ratio()

        # -----------------------------------------------------
        # Signal 3: Token similarity
        # -----------------------------------------------------

        token_score = self._token_similarity(
            query,
            candidate,
        )

        # -----------------------------------------------------
        # Signal 4: Character n-gram similarity
        # -----------------------------------------------------

        ngram_score = self._ngram_similarity(
            compact_query,
            compact_candidate,
        )

        # -----------------------------------------------------
        # Signal 5: Word-boundary similarity
        # -----------------------------------------------------

        boundary_score = self._word_boundary_similarity(
            query,
            candidate,
        )

        # -----------------------------------------------------
        # Signal 6: Anchored token similarity
        # -----------------------------------------------------

        anchored_score = self._anchored_token_similarity(
            query,
            candidate,
        )

        # -----------------------------------------------------
        # Signal 7: Phonetic similarity
        # -----------------------------------------------------

        phonetic_score = self._phonetic_similarity(
            query,
            candidate,
        )

        # -----------------------------------------------------
        # Combined score
        # -----------------------------------------------------

        score = (
            sequence_score * 0.05
            + compact_score * 0.20
            + token_score * 0.10
            + ngram_score * 0.15
            + boundary_score * 0.10
            + phonetic_score * 0.15
            + anchored_score * 0.25
        )

        return score

    # =========================================================
    # TOKEN MATCHING
    # =========================================================

    def _token_similarity(
        self,
        first: str,
        second: str,
    ) -> float:

        first_tokens = first.split()
        second_tokens = second.split()

        if not first_tokens or not second_tokens:
            return 0.0

        scores: list[float] = []

        for first_token in first_tokens:

            best = 0.0

            for second_token in second_tokens:

                score = SequenceMatcher(
                    None,
                    first_token,
                    second_token,
                ).ratio()

                if score > best:
                    best = score

            scores.append(best)

        return sum(scores) / len(scores)

    # =========================================================
    # WORD-BOUNDARY MATCHING
    # =========================================================

    def _word_boundary_similarity(
        self,
        query: str,
        candidate: str,
    ) -> float:

        query_tokens = query.split()

        if not query_tokens:
            return 0.0

        compact_candidate = self._compact(candidate)

        if not compact_candidate:
            return 0.0

        compact_query = self._compact(query)

        if compact_query == compact_candidate:
            return 1.0

        token_scores: list[float] = []

        for token in query_tokens:

            if not token:
                continue

            best = 0.0

            if token in compact_candidate:
                best = 1.0

            token_length = len(token)

            min_length = max(
                1,
                token_length - 1,
            )

            max_length = min(
                len(compact_candidate),
                token_length + 1,
            )

            for window_length in range(
                min_length,
                max_length + 1,
            ):
                for index in range(
                    len(compact_candidate)
                    - window_length
                    + 1
                ):
                    window = compact_candidate[
                        index:index + window_length
                    ]

                    score = SequenceMatcher(
                        None,
                        token,
                        window,
                    ).ratio()

                    if score > best:
                        best = score

            token_scores.append(best)

        if not token_scores:
            return 0.0

        return sum(token_scores) / len(token_scores)

    # =========================================================
    # ANCHORED TOKEN MATCHING
    # =========================================================

    def _anchored_token_similarity(
        self,
        query: str,
        candidate: str,
    ) -> float:

        query_tokens = query.split()

        if len(query_tokens) != 2:
            return 0.0

        candidate_compact = self._compact(candidate)

        if not candidate_compact:
            return 0.0

        first_token = query_tokens[0]
        second_token = query_tokens[1]

        best_score = 0.0

        for split_index in range(
            1,
            len(candidate_compact),
        ):
            candidate_first = candidate_compact[
                :split_index
            ]

            candidate_second = candidate_compact[
                split_index:
            ]

            first_score = SequenceMatcher(
                None,
                first_token,
                candidate_first,
            ).ratio()

            second_score = SequenceMatcher(
                None,
                second_token,
                candidate_second,
            ).ratio()

            score = (
                first_score * 0.60
                + second_score * 0.40
            )

            if score > best_score:
                best_score = score

        return best_score

    # =========================================================
    # PHONETIC MATCHING
    # =========================================================

    def _phonetic_similarity(
        self,
        first: str,
        second: str,
    ) -> float:

        first_compact = self._compact(first)
        second_compact = self._compact(second)

        if not first_compact or not second_compact:
            return 0.0

        first_phonetic = self._phonetic_encode(
            first_compact
        )

        second_phonetic = self._phonetic_encode(
            second_compact
        )

        compact_score = SequenceMatcher(
            None,
            first_phonetic,
            second_phonetic,
        ).ratio()

        first_tokens = first.split()
        second_tokens = second.split()

        token_score = 0.0

        if first_tokens and second_tokens:

            token_matches: list[float] = []

            for first_token in first_tokens:

                encoded_first = self._phonetic_encode(
                    first_token
                )

                best = 0.0

                for second_token in second_tokens:

                    encoded_second = self._phonetic_encode(
                        second_token
                    )

                    score = SequenceMatcher(
                        None,
                        encoded_first,
                        encoded_second,
                    ).ratio()

                    if score > best:
                        best = score

                token_matches.append(best)

            if token_matches:
                token_score = (
                    sum(token_matches)
                    / len(token_matches)
                )

        return (
            compact_score * 0.60
            + token_score * 0.40
        )

    @staticmethod
    def _phonetic_encode(
        text: str,
    ) -> str:

        text = "".join(
            character
            for character in text.lower()
            if character.isalpha()
        )

        if not text:
            return ""

        encoded = text[0]

        groups = {
            "bfpv": "1",
            "cgjkqsxz": "2",
            "dt": "3",
            "l": "4",
            "mn": "5",
            "r": "6",
        }

        def code(character: str) -> str:
            for letters, value in groups.items():
                if character in letters:
                    return value

            return "0"

        previous = code(text[0])

        for character in text[1:]:

            current = code(character)

            if current == "0":
                previous = current
                continue

            if current != previous:
                encoded += current

            previous = current

            if len(encoded) >= 8:
                break

        return encoded[:8]

    # =========================================================
    # N-GRAM MATCHING
    # =========================================================

    @staticmethod
    def _ngrams(
        text: str,
        size: int = 3,
    ) -> set[str]:

        if len(text) < size:
            return {text}

        return {
            text[index:index + size]
            for index in range(
                len(text) - size + 1
            )
        }

    def _ngram_similarity(
        self,
        first: str,
        second: str,
    ) -> float:

        if not first or not second:
            return 0.0

        first_ngrams = self._ngrams(first)
        second_ngrams = self._ngrams(second)

        if not first_ngrams or not second_ngrams:
            return 0.0

        intersection = (
            first_ngrams & second_ngrams
        )

        union = (
            first_ngrams | second_ngrams
        )

        if not union:
            return 0.0

        return len(intersection) / len(union)

    # =========================================================
    # TEXT NORMALIZATION
    # =========================================================

    @classmethod
    def _remove_action_prefix(
        cls,
        text: str,
    ) -> str:

        words = text.split()

        if not words:
            return ""

        if words[0] in cls.ACTION_WORDS:
            return " ".join(words[1:])

        return text

    @staticmethod
    def _compact(
        text: str,
    ) -> str:

        return "".join(
            character
            for character in text.lower()
            if character.isalnum()
        )

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        return " ".join(
            text.lower().strip().split()
        )

    # =========================================================
    # DEBUG
    # =========================================================

    def debug_candidates(
        self,
        text: str,
        limit: int = 10,
    ) -> list[dict[str, float | str]]:

        normalized = self._normalize(text)

        if not normalized:
            return []

        command = self._remove_action_prefix(
            normalized
        )

        if not command:
            return []

        results: list[dict[str, float | str]] = []

        for application in self.registry.all():

            candidates = (
                application.name,
                *application.aliases,
            )

            for candidate in candidates:

                candidate_normalized = self._normalize(
                    candidate
                )

                if not candidate_normalized:
                    continue

                compact_query = self._compact(command)
                compact_candidate = self._compact(
                    candidate_normalized
                )

                sequence_score = SequenceMatcher(
                    None,
                    command,
                    candidate_normalized,
                ).ratio()

                compact_score = SequenceMatcher(
                    None,
                    compact_query,
                    compact_candidate,
                ).ratio()

                token_score = self._token_similarity(
                    command,
                    candidate_normalized,
                )

                ngram_score = self._ngram_similarity(
                    compact_query,
                    compact_candidate,
                )

                boundary_score = (
                    self._word_boundary_similarity(
                        command,
                        candidate_normalized,
                    )
                )

                anchored_score = (
                    self._anchored_token_similarity(
                        command,
                        candidate_normalized,
                    )
                )

                phonetic_score = (
                    self._phonetic_similarity(
                        command,
                        candidate_normalized,
                    )
                )

                combined_score = (
                    sequence_score * 0.05
                    + compact_score * 0.20
                    + token_score * 0.10
                    + ngram_score * 0.15
                    + boundary_score * 0.10
                    + phonetic_score * 0.15
                    + anchored_score * 0.25
                )

                results.append(
                    {
                        "application": application.name,
                        "candidate": candidate_normalized,
                        "sequence": sequence_score,
                        "compact": compact_score,
                        "token": token_score,
                        "ngram": ngram_score,
                        "boundary": boundary_score,
                        "anchored": anchored_score,
                        "phonetic": phonetic_score,
                        "combined": combined_score,
                    }
                )

        results.sort(
            key=lambda item: float(
                item["combined"]
            ),
            reverse=True,
        )

        return results[:limit]