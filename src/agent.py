from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "I could not find relevant information in the knowledge base."

        context_parts = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or metadata.get("doc_id", "unknown")
            context_parts.append(f"[{index}] Source: {source}\n{result['content']}")

        prompt = (
            "You are a knowledge-base assistant. Answer the question using only the provided context. "
            "If the context does not contain enough information, say that clearly. "
            "Cite the supporting context numbers such as [1] or [2].\n\n"
            f"Context:\n{chr(10).join(context_parts)}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
