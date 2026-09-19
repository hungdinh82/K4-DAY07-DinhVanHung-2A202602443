from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:\s+|\n+)", text.strip())
            if sentence.strip()
        ]
        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk]).strip()
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text.strip(), self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]

        separator = next(
            (candidate for candidate in remaining_separators if candidate and candidate in current_text),
            None,
        )
        if separator is None:
            # No usable separator remains: make a guaranteed-progress split.
            return [
                current_text[start : start + self.chunk_size].strip()
                for start in range(0, len(current_text), self.chunk_size)
                if current_text[start : start + self.chunk_size].strip()
            ]

        separator_index = remaining_separators.index(separator)
        parts = [part.strip() for part in current_text.split(separator) if part.strip()]
        smaller_separators = remaining_separators[separator_index + 1 :]
        pieces: list[str] = []
        for part in parts:
            if len(part) > self.chunk_size:
                pieces.extend(self._split(part, smaller_separators))
            else:
                pieces.append(part)

        chunks: list[str] = []
        current = ""
        for piece in pieces:
            candidate = piece if not current else f"{current}{separator}{piece}"
            if current and len(candidate) > self.chunk_size:
                chunks.append(current.strip())
                current = piece
            else:
                current = candidate
        if current:
            chunks.append(current.strip())
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
