"""Text cleaning, splitting, and hashing utilities."""

import hashlib
import re


def clean_text(text: str) -> str:
    """Clean transcribed text: normalize whitespace, fix common ASR artifacts."""
    text = text.strip()
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    # Remove filler words common in ASR output
    text = re.sub(r"\b(um|uh|hmm|hm)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_text_for_tts(text: str, max_chars: int = 350) -> list[str]:
    """Split text into chunks suitable for XTTS (max ~350 chars).

    Splits on sentence boundaries first, then on clause boundaries
    if individual sentences are too long.
    """
    if len(text) <= max_chars:
        return [text]

    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(sentence) > max_chars:
            # Split long sentence on clause boundaries
            if current:
                chunks.append(current.strip())
                current = ""
            clauses = re.split(r"(?<=[,;:])\s+", sentence)
            for clause in clauses:
                if len(current) + len(clause) + 1 <= max_chars:
                    current = f"{current} {clause}".strip()
                else:
                    if current:
                        chunks.append(current.strip())
                    current = clause
        elif len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current.strip())
            current = sentence

    if current:
        chunks.append(current.strip())

    return [c for c in chunks if c]


def text_hash(text: str) -> str:
    """SHA-256 hash of text, for cache keys."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def segment_cache_key(speaker_id: str, text: str) -> str:
    """Generate a cache key for a TTS segment."""
    return f"{speaker_id}_{text_hash(text)}"
