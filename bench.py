from __future__ import annotations

import re
from pathlib import Path

from src import (
    ChunkingStrategyComparator,
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
)


DATA_DIR = Path("data/library-borrowing")
CHUNK_SIZE = 500


def read_markdown(path: Path) -> tuple[dict[str, str], str]:
    """Read simple YAML-like frontmatter without adding a YAML dependency."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text.strip()

    _, frontmatter, body = text.split("---", 2)
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, body.strip()


class HeadingChunker:
    """Keep Markdown sections together and retain their heading as context."""

    def __init__(self, chunk_size: int = CHUNK_SIZE) -> None:
        self.chunk_size = chunk_size
        self._recursive = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        starts = [match.start() for match in re.finditer(r"(?m)^##\s+", text)]
        if not starts:
            return self._recursive.chunk(text)

        boundaries = [0, *starts, len(text)]
        sections = [
            text[boundaries[index] : boundaries[index + 1]].strip()
            for index in range(len(boundaries) - 1)
        ]
        chunks: list[str] = []
        for section in sections:
            if not section:
                continue
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue

            lines = section.splitlines()
            heading = lines[0].strip() if lines and lines[0].startswith("##") else ""
            body = "\n".join(lines[1:]).strip() if heading else section
            pieces = self._recursive.chunk(body)
            chunks.extend(f"{heading}\n{piece}".strip() if heading else piece for piece in pieces)
        return chunks


# Change only this line when comparing a different personal strategy.
CHUNKER = HeadingChunker(chunk_size=CHUNK_SIZE)


QUERIES = [
    {
        "question": "How many Short Loan items may be borrowed at once, and how long does each loan last?",
        "gold": "Only two Short Loan items may be borrowed at once, and each Short Loan lasts 3 hours.",
        "doc_id": "borrowing-limits",
        "metadata_filter": None,
        "gold_phrases": ["two Short Loan", "3 hours"],
    },
    {
        "question": "Under what conditions may a General Collection item be kept for up to 365 days?",
        "gold": "There must be no recall, the borrower's enrolment or membership must remain current, and the borrowing record must have no fines or blocks.",
        "doc_id": "borrowing-terms",
        "metadata_filter": None,
        "gold_phrases": ["recalled the item", "enrolment or membership", "no fines or blocks"],
    },
    {
        "question": "How do I request a digital copy of a journal article or book chapter?",
        "gold": "Sign in to the catalogue, select the journal and location, choose Request a digital copy, complete the form and copyright acknowledgement, and submit the request.",
        "doc_id": "requesting-items",
        "metadata_filter": None,
        "gold_phrases": ["Request a digital copy", "copyright acknowledgement"],
    },
    {
        "question": "Where must a Short Loan item be returned?",
        "gold": "A Short Loan item must be returned to the location from which it was borrowed.",
        "doc_id": "returning-items",
        "metadata_filter": None,
        "gold_phrases": ["Short Loan item", "location from which it was borrowed"],
    },
    {
        "question": "How many items can I borrow through Resource Sharing in a calendar year, and who is eligible?",
        "gold": "Postgraduate and honours students are eligible, and eligible students may borrow up to 100 items from other institutions per calendar year.",
        "doc_id": "resource-sharing-students",
        "metadata_filter": {"audience": "student"},
        "gold_phrases": ["postgraduate students and honours students", "up to 100 items"],
    },
]


def load_documents(chunker) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(DATA_DIR.glob("*.md")):
        metadata, body = read_markdown(path)
        chunks = chunker.chunk(body)
        source_doc_id = metadata.get("doc_id", path.stem)
        for index, chunk in enumerate(chunks):
            chunk_metadata = {**metadata, "doc_id": source_doc_id, "source": str(path)}
            documents.append(Document(id=f"{source_doc_id}#{index}", content=chunk, metadata=chunk_metadata))
    return documents


def print_baseline() -> None:
    print("=== Baseline: built-in chunking strategies ===")
    for path in sorted(DATA_DIR.glob("*.md"))[:3]:
        _, body = read_markdown(path)
        comparison = ChunkingStrategyComparator().compare(body, chunk_size=CHUNK_SIZE)
        print(f"\n{path}")
        for strategy, stats in comparison.items():
            print(f"  {strategy}: count={stats['count']} avg_length={stats['avg_length']:.1f}")


def content_matches(result: dict, query: dict) -> bool:
    content = result["content"].lower()
    return all(phrase.lower() in content for phrase in query["gold_phrases"])


def evaluate(store: EmbeddingStore, query: dict, metadata_filter: dict | None) -> tuple[list[dict], int]:
    results = store.search_with_filter(query["question"], top_k=3, metadata_filter=metadata_filter)
    content_hits = [result for result in results if content_matches(result, query)]
    if not content_hits:
        points = 0
    else:
        rank = results.index(content_hits[0]) + 1
        points = 2 if rank == 1 else 1
    return results, points


def print_results(label: str, query_number: int, query: dict, results: list[dict], points: int, metadata_filter: dict | None) -> None:
    print(f"\n[{label}] Q{query_number}: {query['question']}")
    print(f"Filter: {metadata_filter or 'none'} | points={points}/2")
    for rank, result in enumerate(results, start=1):
        doc_match = result["metadata"].get("doc_id") == query["doc_id"]
        phrase_match = content_matches(result, query)
        print(
            f"  {rank}. score={result['score']:.4f} "
            f"doc_id={result['metadata'].get('doc_id')} chunk={result['id']} "
            f"doc_match={doc_match} content_match={phrase_match}"
        )
        print(f"     {result['content'][:180].replace(chr(10), ' ')}...")


def main() -> int:
    print_baseline()

    strategies = {
        "fixed_size": FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=50),
        "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
        "recursive": RecursiveChunker(chunk_size=CHUNK_SIZE),
        "personal_heading": CHUNKER,
    }
    for label, chunker in strategies.items():
        documents = load_documents(chunker)
        store = EmbeddingStore(collection_name=f"library_{label}")
        store.add_documents(documents)
        print(f"\n=== Strategy: {label} ({chunker.__class__.__name__}) ===")
        print(f"Loaded {len(documents)} chunks from {len(list(DATA_DIR.glob('*.md')))} documents")
        total_points = 0
        for index, query in enumerate(QUERIES, start=1):
            results, points = evaluate(store, query, query["metadata_filter"])
            total_points += points
            print_results(label, index, query, results, points, query["metadata_filter"])

        # Required A/B comparison for the query whose answer depends on audience.
        filtered_query = QUERIES[4]
        unfiltered_results, unfiltered_points = evaluate(store, filtered_query, None)
        print_results(label, 5, filtered_query, unfiltered_results, unfiltered_points, None)
        print(f"Summary {label}: {total_points}/10 with filter; Q5 A/B filter={2 if evaluate(store, filtered_query, filtered_query['metadata_filter'])[1] > unfiltered_points else unfiltered_points}/2 vs no filter={unfiltered_points}/2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
