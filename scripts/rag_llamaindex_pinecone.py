#!/usr/bin/env python3
"""LlamaIndex + Pinecone RAG ingestion helper.

This script reads CSV sources, converts rows to documents, builds a LlamaIndex
GPTVectorStoreIndex, and stores embeddings in Pinecone.

Example:
  python3 scripts/rag_llamaindex_pinecone.py \
    --source data/customer_feedback.csv \
    --source data/jira_tickets.csv \
    --index product-rag \
    --namespace product-data \
    --upsert

Query example:
  python3 scripts/rag_llamaindex_pinecone.py \
    --source data/customer_feedback.csv \
    --source data/jira_tickets.csv \
    --index product-rag \
    --namespace product-data \
    --upsert \
    --query "What retention risks do we see?"
"""

import argparse
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import pandas as pd
import pinecone
from pinecone import ServerlessSpec
from llama_index.core import GPTVectorStoreIndex
from llama_index.core.schema import Document
from llama_index.core.storage.storage_context import StorageContext
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore

load_dotenv()

DEFAULT_DIMENSION = 1536
DEFAULT_METRIC = 'cosine'
DEFAULT_INDEX = 'product-rag'


def clean_text(text: str) -> str:
    if text is None:
        return ''
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    return cleaned


def build_document(row: pd.Series, source_name: str, idx: int) -> Optional[Document]:
    text_fields = []
    for field in ['feedback_text', 'summary', 'insight', 'issue', 'notes', 'trend', 'feedback', 'description', 'details']:
        if field in row and pd.notna(row[field]):
            text_fields.append(str(row[field]))
    if not text_fields:
        text_fields = [clean_text(' '.join([str(v) for v in row.values if isinstance(v, str) and v.strip()]))]
    text = clean_text(' '.join(text_fields))
    if not text:
        return None

    metadata = {'source': source_name}
    for key, value in row.items():
        if key and pd.notna(value):
            metadata[str(key)] = str(value)

    return Document(text=text, doc_id=f"{source_name}-{idx+1}", extra_info=metadata)


def load_sources(source_paths: List[str], limit: Optional[int] = None) -> List[Document]:
    documents: List[Document] = []
    for path in source_paths:
        source_name = os.path.splitext(os.path.basename(path))[0]
        df = pd.read_csv(path)
        if limit is not None:
            df = df.head(limit)
        for idx, row in df.iterrows():
            doc = build_document(row, source_name, idx)
            if doc is not None:
                documents.append(doc)
    return documents


def get_openai_embedding(api_key: str) -> OpenAIEmbedding:
    return OpenAIEmbedding(api_key=api_key)


def get_openai_llm(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def initialize_pinecone(index_name: str, env: str, api_key: str, dimension: int = DEFAULT_DIMENSION) -> Any:
    pc = pinecone.Pinecone(api_key=api_key)
    existing_indexes = pc.list_indexes()
    existing_names = [idx.name for idx in existing_indexes]
    if index_name not in existing_names:
        print(f'Creating Pinecone index {index_name} with dimension={dimension}')
        spec = ServerlessSpec(cloud='aws', region='us-east-1')
        pc.create_index(name=index_name, spec=spec, dimension=dimension, metric=DEFAULT_METRIC)
    else:
        print(f'Using existing Pinecone index {index_name}')
    pinecone_index = pc.Index(index_name)
    return pinecone_index


def build_vector_store(pinecone_index: Any, api_key: str, index_name: str, namespace: str) -> PineconeVectorStore:
    return PineconeVectorStore(
        pinecone_index=pinecone_index,
        api_key=api_key,
        index_name=index_name,
        namespace=namespace,
    )


def create_index(documents: List[Document], vector_store: PineconeVectorStore) -> GPTVectorStoreIndex:
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = GPTVectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)
    return index


def query_index(index: GPTVectorStoreIndex, prompt: str, openai_api_key: str, top_k: int = 5) -> str:
    llm = get_openai_llm(openai_api_key)
    query_engine = index.as_query_engine(llm=llm, similarity_top_k=top_k)
    response = query_engine.query(prompt)
    return str(response)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', action='append', required=True, help='Path to CSV file to ingest. Repeat for multiple files.')
    parser.add_argument('--limit', type=int, default=None, help='Max rows to ingest per source.')
    parser.add_argument('--index', default=DEFAULT_INDEX, help='Pinecone index name.')
    parser.add_argument('--namespace', default='', help='Pinecone namespace.')
    parser.add_argument('--dry-run', action='store_true', help='Do not upsert to Pinecone; only simulate ingestion.')
    parser.add_argument('--upsert', action='store_true', help='Upsert documents into Pinecone.')
    parser.add_argument('--query', type=str, default=None, help='Ask a question against the created index after upsert.')
    parser.add_argument('--top-k', type=int, default=5, help='Top-k retrieval for query.')
    return parser.parse_args()


def main():
    args = parse_args()
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    pinecone_api_key = os.environ.get('PINECONE_API_KEY')
    pinecone_env = os.environ.get('PINECONE_ENV')

    if not openai_api_key:
        raise ValueError('Missing OPENAI_API_KEY in environment. Set it in .env or the shell.')
    if not pinecone_api_key:
        raise ValueError('Missing PINECONE_API_KEY in environment. Set it in .env or the shell.')
    if not pinecone_env:
        raise ValueError('Missing PINECONE_ENV in environment. Set it in .env or the shell.')

    documents = load_sources(args.source, limit=args.limit)
    print(f'Loaded {len(documents)} documents from {len(args.source)} sources.')
    if not documents:
        raise ValueError('No documents were built. Check source CSV content and field names.')

    if args.dry_run:
        print('Dry-run mode: documents will not be upserted to Pinecone.')
        print('Sample document:')
        print(documents[0].to_dict())
        return

    if args.upsert:
        pinecone_index = initialize_pinecone(args.index, pinecone_env, pinecone_api_key)
        vector_store = build_vector_store(pinecone_index, pinecone_api_key, args.index, args.namespace)
        index = create_index(documents, vector_store)
        print('Upsert completed to Pinecone index:', args.index)
        if args.query:
            print('Running query against index...')
            response = query_index(index, args.query, openai_api_key, top_k=args.top_k)
            print('Query response:')
            print(response)
    else:
        print('No upsert requested. Run with --upsert to store documents in Pinecone.')


if __name__ == '__main__':
    main()
