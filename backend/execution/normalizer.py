from __future__ import annotations

import re


class CommandNormalizer:
    """
    Normalizes speech-recognition output before routing.

    The normalizer only performs safe text cleanup.
    It does NOT decide what action the user wants.
    """

    # Common punctuation added by STT.
    TRAILING_PUNCTUATION = re.compile(
        r"[.!?,;:]+$"
    )

    # Common conversational prefixes that can appear
    # around a direct command.
    COMMAND_PREFIXES = (
        "please ",
        "can you ",
        "could you ",
        "would you ",
    )

    def normalize(self, text: str) -> str:
        """
        Normalize recognized speech.

        Example:

            "Please open Chrome."
                ->
            "open chrome"
        """

        if not text:
            return ""

        # -----------------------------------------------------
        # Basic whitespace normalization
        # -----------------------------------------------------

        text = text.strip()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        # -----------------------------------------------------
        # Remove trailing STT punctuation
        # -----------------------------------------------------

        text = self.TRAILING_PUNCTUATION.sub(
            "",
            text,
        )

        # -----------------------------------------------------
        # Normalize case
        # -----------------------------------------------------

        text = text.lower().strip()

        # -----------------------------------------------------
        # Remove safe conversational prefixes
        # -----------------------------------------------------

        for prefix in self.COMMAND_PREFIXES:
            if text.startswith(prefix):
                text = text[len(prefix):]
                break

        return text.strip()