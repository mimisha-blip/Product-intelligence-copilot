#!/usr/bin/env python3
"""
RAG Pipeline using LlamaIndex + Pinecone + Local Sentence-Transformers Embeddings
- Uses all-MiniLM-L6-v2 model for local embeddings (no API quota issues)
- Ingests CSV data into Pinecone vector store
- Supports semantic search and retrieval
"""

import argparse
import os
import sys
from typing import Any, List
import pandas as pd
import pinecone
from pinecone import ServerlessSpec
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DIMENSION = 384  # all-MiniLM-L6-v2 output dimension
DEFAULT_METRIC = 'cosine'
DEFAULT_INDEX = 'product-rag'


def build_document(row: dict, source_name: str, idx: int) -> Document:
    """Convert CSV row to LlamaIndex Document with metadata."""
    doc_id = f"{source_name.lower()}_{idx}"
    text_fields = [str(v) for k, v in row.items() if v and k not in ['id', 'key', 'case_number', 'competitor']]
    text = ' | '.join(text_fields)
    doc = Document(
        id_=doc_id,
        text=text,
        metadata=row
    )
    return doc


def load_sources(source_paths: List[str], limit: int = None) -> List[Document]:
    """Load CSV files and convert to LlamaIndex Documents."""
    documents = []
    for source_path in source_paths:
        if not os.path.exists(source_path):
            print(f"Warning: Source file not found: {source_path}")
            continue
        df = pd.read_csv(source_path)
        if limit:
            df = df.head(limit)
        source_name = os.path.splitext(os.path.basename(source_path))[0]
        for idx, row in df.iterrows():
            doc = build_document(row.to_dict(), source_name, idx)
            documents.append(doc)
    print(f"Loaded {len(documents)} documents from {len(source_paths)} sources.")
    return documents


def get_huggingface_embedding():
    """Get HuggingFace embedding model (all-MiniLM-L6-v2)."""
    print("Initializing HuggingFace embedding model (all-MiniLM-L6-v2)...")
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        cache_folder=".cache"
    )
    return embed_model


def initialize_pinecone(index_name: str, api_key: str, dimension: int = DEFAULT_DIMENSION) -> Any:
    """Initialize Pinecone client and ensure index exists."""
    pc = pinecone.Pinecone(api_key=api_key)
    existing_indexes = pc.list_indexes()
    existing_names = [idx.name for idx in existing_indexes]
    if index_name not in existing_names:
        print(f'Creating Pinecone index {index_name} with dimension={dimension}')
        spec = ServerlessSpec(cloud='aws', region='us-east-1')
        pc.create_index(name=index_name, spec=spec, dimension=dimension, metric=DEFAULT_METRIC)
        print(f'Index {index_name} created successfully')
    else:
        print(f'Using existing Pinecone index {index_name}')
    pinecone_index = pc.Index(index_name)
    return pinecone_index


def build_vector_store(pinecone_index: Any, index_name: str, namespace: str = "") -> PineconeVectorStore:
    """Create PineconeVectorStore instance."""
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index,
        namespace=namespace
    )
    return vector_store


def create_index(documents: List[Document], vector_store: PineconeVectorStore, embed_model: Any) -> VectorStoreIndex:
    """Build VectorStoreIndex from documents."""
    print(f"Creating VectorStoreIndex with {len(documents)} documents...")
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True
    )
    print("Index created and persisted to Pinecone successfully!")
    return index


def query_index(index: VectorStoreIndex, query_text: str, top_k: int = 5) -> str:
    """Execute query against index."""
    print(f"\nQuerying index for: '{query_text}'")
    query_engine = index.as_query_engine(similarity_top_k=top_k)
    response = query_engine.query(query_text)
    return str(response)


def main():
    parser = argparse.ArgumentParser(description="RAG Pipeline with Local Embeddings + Pinecone")
    parser.add_argument('--source', action='append', help='CSV file path to ingest (can specify multiple times)')
    parser.add_argument('--limit', type=int, help='Max rows per source')
    parser.add_argument('--index', default=DEFAULT_INDEX, help='Pinecone index name')
    parser.add_argument('--namespace', default='', help='Pinecone namespace')
    parser.add_argument('--dry-run', action='store_true', help='Skip Pinecone upsert, only validate documents')
    parser.add_argument('--upsert', action='store_true', help='Actually upload to Pinecone')
    parser.add_argument('--query', help='Execute query after upsert')
    parser.add_argument('--top-k', type=int, default=5, help='Retrieval depth for query')
    args = parser.parse_args()

    if not args.source:
        parser.error("--source is required")

    # Load documents
    documents = load_sources(args.source, limit=args.limit)
    if args.dry_run:
        print(f"\nDry-run mode: {len(documents)} documents will not be upserted to Pinecone.")
        print(f"Sample document:")
        if documents:
            doc = documents[0]
            print(f"  ID: {doc.id_}")
            print(f"  Text: {doc.text[:100]}...")
            print(f"  Metadata keys: {list(doc.metadata.keys())}")
        return

    # Initialize infrastructure
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    if not pinecone_api_key:
        print("Error: PINECONE_API_KEY not set in .env")
        sys.exit(1)

    if args.upsert:
        pinecone_index = initialize_pinecone(args.index, pinecone_api_key)
        vector_store = build_vector_store(pinecone_index, args.index, args.namespace)
        embed_model = get_huggingface_embedding()
        index = create_index(documents, vector_store, embed_model)
        if args.query:
            response = query_index(index, args.query, args.top_k)
            print(f"\nResponse:\n{response}")
    else:
        print("Provide --upsert flag to upload to Pinecone")


if __name__ == '__main__':
    main()
