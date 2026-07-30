"""Text cleaning and normalization utilities."""

import re
import unicodedata


def clean_text(text: str) -> str:
    """Clean and normalize extracted text."""
    # Normalize unicode (full-width to half-width, etc.)
    text = unicodedata.normalize("NFKC", text)

    # Remove excessive whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove control characters except newlines
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # Normalize Chinese punctuation spacing
    text = re.sub(r"\s*([，。；：！？、])", r"\1", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)

    return text.strip()
