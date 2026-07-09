#!/usr/bin/env python3
"""RAG pipeline: clean, metadata, chunk, embed, store (Pinecone), retrieve.

Usage examples:
  python3 src/legacy/rag_pipeline_legacy.py --source data/raw/customer_feedback.csv --limit 2 --dry-run
  python3 src/legacy/rag_pipeline_legacy.py --source data/raw/customer_feedback.csv --limit 50 --upsert --index my-rag-index

Requires: sentence-transformers, pandas, pinecone-client (only for upsert)
"""

import argparse
import csv
import os
import re
import sys
from typing import List, Dict, Any

from dotenv import load_dotenv
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

try:
    import pinecone
except Exception:
    pinecone = None

load_dotenv()


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ''
    # basic cleaning: normalize whitespace, remove control chars
    text = re.sub(r"\s+", " ", text).strip()
    return text


def add_metadata(row: Dict[str, Any], source_name: str) -> Dict[str, Any]:
    # Example metadata - include source, row index and key fields if present
    meta = {
        'source': source_name,
    }
    # Copy some common fields if present
    for key in ['feedback_id', 'id', 'case_number', 'key', 'customer', 'customer_segment', 'feature', 'created_at', 'date', 'source_date', 'metric', 'period']:
        if key in row and not pd.isna(row[key]):
            meta[key] = str(row[key])
    return meta


def chunk_text(text: str, max_words: int = 120) -> List[str]:
    # Split into sentences then assemble into chunks up to max_words
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ''
    current_words = 0
    for s in sentences:
        words = len(s.split())
        if current_words + words <= max_words:
            if current:
                current += ' ' + s
            else:
                current = s
            current_words += words
        else:
            if current:
                chunks.append(current.strip())
            current = s
            current_words = words
    if current:
        chunks.append(current.strip())
    # Fallback: if no sentences, return the text
    if not chunks and text:
        return [text]
    return chunks


class RAGPipeline:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        print(f'Loading embedding model: {model_name}')
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    def process_csv(self, path: str, source_label: str = None, limit: int = None) -> List[Dict[str, Any]]:
        df = pd.read_csv(path)
        if limit:
            df = df.head(limit)
        docs = []
        for idx, row in df.iterrows():
            # prefer a primary text field if present
            text_fields = []
            # common heuristics for which text to use
            for f in ['feedback_text', 'summary', 'insight', 'issue', 'notes', 'trend', 'feedback', 'details']:
                if f in row and not pd.isna(row[f]):
                    text_fields.append(str(row[f]))
            # fallback: join all string columns
            if not text_fields:
                text_fields = [', '.join([str(x) for x in row.values if isinstance(x, str) and x.strip()])]

            full_text = ' '.join(text_fields)
            clean = clean_text(full_text)
            meta = add_metadata(row, source_label or os.path.basename(path))
            chunks = chunk_text(clean)
            for ci, c in enumerate(chunks):
                docs.append({
                    'id': f"{os.path.splitext(os.path.basename(path))[0]}-{idx+1}-{ci+1}",
                    'text': c,
                    'metadata': {**meta, 'chunk_index': ci+1},
                })
        return docs

    def upsert_to_pinecone(self, index_name: str, vectors: List[np.ndarray], metas: List[Dict[str, Any]], ids: List[str], namespace: str = ''):
        if pinecone is None:
            raise RuntimeError('pinecone-client is not installed or not available in this environment')
        api_key = os.environ.get('PINECONE_API_KEY')
        env = os.environ.get('PINECONE_ENV')
        if not api_key or not env:
            raise RuntimeError('Set PINECONE_API_KEY and PINECONE_ENV environment variables to upsert')
        pinecone.init(api_key=api_key, environment=env)

        # create index if not exists
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(index_name, dimension=self.dim)
        idx = pinecone.Index(index_name)

        # Pinecone expects list of tuples (id, vector, metadata)
        to_upsert = [(ids[i], vectors[i].tolist(), metas[i]) for i in range(len(ids))]
        # Batch upsert in chunks
        batch_size = 100
        for i in range(0, len(to_upsert), batch_size):
            batch = to_upsert[i:i+batch_size]
            idx.upsert(vectors=batch, namespace=namespace)

    def retrieve_from_pinecone(self, index_name: str, query_text: str, top_k: int = 5, namespace: str = '') -> List[Dict[str, Any]]:
        if pinecone is None:
            raise RuntimeError('pinecone-client is not installed or not available in this environment')
        api_key = os.environ.get('PINECONE_API_KEY')
        env = os.environ.get('PINECONE_ENV')
        if not api_key or not env:
            raise RuntimeError('Set PINECONE_API_KEY and PINECONE_ENV environment variables to query')
        pinecone.init(api_key=api_key, environment=env)
        if index_name not in pinecone.list_indexes():
            raise RuntimeError(f'Index {index_name} does not exist')
        idx = pinecone.Index(index_name)
        q_emb = self.embed_texts([query_text])[0].tolist()
        res = idx.query(vector=q_emb, top_k=top_k, include_metadata=True, namespace=namespace)
        return res.get('matches', [])


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--source', action='append', required=True, help='Path to source CSV file. Repeat for multiple files.')
    p.add_argument('--limit', type=int, default=None, help='Limit rows to process per file')
    p.add_argument('--model', default='all-MiniLM-L6-v2', help='SentenceTransformer model')
    p.add_argument('--upsert', action='store_true', help='Upsert vectors to Pinecone (requires env vars)')
    p.add_argument('--index', default='product-rag', help='Pinecone index name')
    p.add_argument('--namespace', default='', help='Pinecone namespace')
    p.add_argument('--dry-run', action='store_true', help='Only process and embed locally, do not upsert')
    p.add_argument('--topk', type=int, default=5, help='Top-k retrieval size for quick test')
    return p.parse_args()


def main():
    args = parse_args()
    pipeline = RAGPipeline(model_name=args.model)
    docs = []
    for source_path in args.source:
        processed = pipeline.process_csv(source_path, source_label=os.path.basename(source_path), limit=args.limit)
        print(f'Processed {len(processed)} text chunks from {source_path}')
        docs.extend(processed)

    print(f'Total chunks across sources: {len(docs)}')
    texts = [d['text'] for d in docs]
    ids = [d['id'] for d in docs]
    metas = [d['metadata'] for d in docs]

    if not texts:
        print('No text to embed. Exiting.')
        return

    print('Creating embeddings...')
    vectors = pipeline.embed_texts(texts)
    print('Embeddings created. shape=', vectors.shape)

    if args.dry_run:
        # store locally for inspection
        out_vectors = {
            'ids': ids,
            'vectors': vectors.tolist(),
            'metas': metas,
        }
        import json
        base_name = '_'.join([os.path.splitext(os.path.basename(s))[0] for s in args.source])
        os.makedirs('data/processed', exist_ok=True)
        out_path = f'data/processed/dryrun_{base_name}.json'
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(out_vectors, f)
        print('Dry-run saved to', out_path)
        # quick local retrieval test using cosine similarity
        if args.topk > 0:
            q = texts[0]
            qv = pipeline.embed_texts([q])[0]
            sims = (vectors @ qv) / (np.linalg.norm(vectors, axis=1) * np.linalg.norm(qv) + 1e-12)
            top_idx = np.argsort(-sims)[:args.topk]
            print('\nTop local matches for first chunk:')
            for tidx in top_idx:
                print(f'- id={ids[tidx]} score={sims[tidx]:.4f} meta={metas[tidx]}')
        return

    if args.upsert:
        print('Upserting to Pinecone index:', args.index)
        pipeline.upsert_to_pinecone(args.index, vectors, metas, ids, namespace=args.namespace)
        print('Upsert complete.')


if __name__ == '__main__':
    main()
