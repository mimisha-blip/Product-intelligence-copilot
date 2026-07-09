# RAG Pipeline

This folder contains a RAG pipeline that:

- Cleans CSV source data
- Adds metadata
- Chunks documents
- Generates embeddings
- Stores data in Pinecone
- Retrieves relevant context via top-k search

## Setup

1. Install Python dependencies:

```bash
cd '/Users/mimisha/Desktop/Gen Academy/Week2 - RAG/Product data'
python3 -m pip install -r scripts/requirements.txt
python3 -m pip install python-dotenv llama-index llama-index-vector-stores-pinecone llama-index-embeddings-openai pinecone
```

2. Copy `.env.example` to `.env` and set your Pinecone credentials:

```bash
cp .env.example .env
```

3. Edit `.env` if needed:

```env
PINECONE_API_KEY=your_api_key_here
PINECONE_ENV=your_pinecone_env_here
```

## Run dry-run

```bash
python3 scripts/rag_pipeline.py --source data/customer_feedback.csv --dry-run --limit 2
```

## Upsert to Pinecone

```bash
python3 scripts/rag_pipeline.py --source data/customer_feedback.csv --source data/jira_tickets.csv --upsert --index product-rag --namespace prod
```

## Retrieve matches

This script currently supports upsert and local dry-run validation; retrieval is available via the Pinecone client method in `RAGPipeline.retrieve_from_pinecone()`.
