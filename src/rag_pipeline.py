#!/usr/bin/env python3
"""Build and test a Pinecone-backed retrieval index for Product Intelligence Copilot."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Iterable

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ingest_data import load_documents


EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384
DEFAULT_BATCH_SIZE = 100
DEFAULT_TOP_K = 5
DEFAULT_CLOUD = "aws"
DEFAULT_REGION = "us-east-1"
DEFAULT_QUERIES = [
    "What are the top customer pain points?",
    "Which features should we prioritize?",
    "Generate a Q3 roadmap.",
    "What are competitors doing that we are not?",
]


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing {name}. Add it to .env or export it in your shell.")
    return value


def load_environment() -> tuple[str, str]:
    load_dotenv(PROJECT_ROOT / ".env")
    pinecone_api_key = require_env("PINECONE_API_KEY")
    index_name = require_env("PINECONE_INDEX_NAME")
    return pinecone_api_key, index_name


def batch_items(items: list[Any], batch_size: int) -> Iterable[list[Any]]:
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def index_exists(pc: Pinecone, index_name: str) -> bool:
    return index_name in [index_info.name for index_info in pc.list_indexes()]


def existing_index_dimension(pc: Pinecone, index_name: str) -> int | None:
    for index_info in pc.list_indexes():
        if index_info.name == index_name:
            return getattr(index_info, "dimension", None)
    return None


def ensure_pinecone_index(pc: Pinecone, index_name: str) -> Any:
    dimension = existing_index_dimension(pc, index_name)
    if dimension is None:
        pc.create_index(
            name=index_name,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=os.environ.get("PINECONE_CLOUD", DEFAULT_CLOUD),
                region=os.environ.get("PINECONE_REGION", DEFAULT_REGION),
            ),
        )
    elif dimension != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Pinecone index '{index_name}' has dimension {dimension}, but "
            f"{EMBEDDING_MODEL} requires dimension {EMBEDDING_DIMENSION}. "
            "Use a new PINECONE_INDEX_NAME or delete/recreate the old index."
        )
    return pc.Index(index_name)


def load_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def normalize_embedding(embedding: Any) -> list[float]:
    if hasattr(embedding, "tolist"):
        return embedding.tolist()
    return list(embedding)


def embed_texts(model: SentenceTransformer, texts: list[str], show_progress_bar: bool = False) -> list[list[float]]:
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=show_progress_bar,
    )
    return [normalize_embedding(embedding) for embedding in embeddings]


def vector_id(document: Any, fallback_index: int) -> str:
    source_type = document.metadata.get("source_type", "unknown")
    document_id = document.metadata.get("id", fallback_index)
    return f"{source_type}-{document_id}"


def vector_metadata(document: Any) -> dict[str, Any]:
    metadata = dict(document.metadata)
    metadata["text"] = document.page_content
    return metadata


def build_vector_db(documents: list[Any] | None = None, batch_size: int = DEFAULT_BATCH_SIZE) -> Any:
    """Load documents, generate local BGE embeddings, and upsert them to Pinecone."""
    pinecone_api_key, index_name = load_environment()
    pc = Pinecone(api_key=pinecone_api_key)
    index = ensure_pinecone_index(pc, index_name)
    model = load_embedding_model()

    docs = documents if documents is not None else load_documents()
    print(f"Loaded {len(docs)} documents.")
    print(f"Generating embeddings with {EMBEDDING_MODEL} ({EMBEDDING_DIMENSION} dimensions).")

    upserted_count = 0
    for batch_number, document_batch in enumerate(batch_items(docs, batch_size), start=1):
        texts = [document.page_content for document in document_batch]
        embeddings = embed_texts(model, texts, show_progress_bar=False)
        vectors = []
        for offset, (document, embedding) in enumerate(zip(document_batch, embeddings), start=1):
            vectors.append({
                "id": vector_id(document, upserted_count + offset),
                "values": embedding,
                "metadata": vector_metadata(document),
            })
        index.upsert(vectors=vectors)
        upserted_count += len(vectors)
        print(f"Upserted batch {batch_number}: {upserted_count}/{len(docs)} documents.")

    print(f"Uploaded {upserted_count} documents to Pinecone index '{index_name}'.")
    return index


def get_retriever(k: int = DEFAULT_TOP_K):
    """Return a callable retriever that embeds queries locally and searches Pinecone."""
    pinecone_api_key, index_name = load_environment()
    pc = Pinecone(api_key=pinecone_api_key)
    index = ensure_pinecone_index(pc, index_name)
    model = load_embedding_model()

    def retrieve(query: str) -> list[dict[str, Any]]:
        query_embedding = embed_texts(model, [query])[0]
        response = index.query(
            vector=query_embedding,
            top_k=k,
            include_metadata=True,
        )
        if isinstance(response, dict):
            return response.get("matches", [])
        return response.matches

    return retrieve


def match_metadata(match: Any) -> dict[str, Any]:
    return match.get("metadata", {}) if isinstance(match, dict) else match.metadata


def match_score(match: Any) -> Any:
    return match.get("score", "") if isinstance(match, dict) else getattr(match, "score", "")


def print_match(match: Any) -> None:
    metadata = match_metadata(match)
    severity_or_priority = metadata.get("severity") or metadata.get("priority") or ""
    print(f"- score: {match_score(match)}")
    print(f"  source_type: {metadata.get('source_type')}")
    print(f"  product_area: {metadata.get('product_area')}")
    print(f"  severity/priority: {severity_or_priority}")
    print(f"  retrieved text: {metadata.get('text', '')}")
    print(f"  metadata: {metadata}")


def test_retrieval(query: str) -> list[dict[str, Any]]:
    print(f"\nQuery: {query}")
    retriever = get_retriever(k=DEFAULT_TOP_K)
    matches = retriever(query)
    print("Retrieved documents:")
    for match in matches:
        print_match(match)
    return matches


def main() -> None:
    build_vector_db()
    for query in DEFAULT_QUERIES:
        test_retrieval(query)


if __name__ == "__main__":
    main()
