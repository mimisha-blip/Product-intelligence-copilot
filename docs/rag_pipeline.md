# RAG Pipeline

This project uses a Pinecone-backed RAG pipeline for Product Intelligence Copilot.

## Data Flow

1. `src/generate_mock_data.py` creates realistic B2B SaaS CSV datasets under `data/raw/`.
2. `src/ingest_data.py` loads each CSV row as a LangChain-style document.
3. `src/rag_pipeline.py` embeds documents with `BAAI/bge-small-en-v1.5`.
4. Pinecone stores and retrieves the embedded documents.
5. `src/graph.py` routes product questions and calls Qwen on Fireworks for grounded answers.
6. `src/app.py` renders the Streamlit UI.

## Setup

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Create a local `.env` file:

```bash
cp .env.example .env
```

Set real values in `.env`:

```env
PINECONE_API_KEY=your_real_pinecone_key
PINECONE_INDEX_NAME=product-intelligence-copilot-bge
FIREWORKS_API_KEY=your_real_fireworks_key
FIREWORKS_MODEL=accounts/fireworks/models/qwen3p7-plus
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

Do not commit `.env`; it is ignored by Git.

## Commands

Generate mock datasets:

```bash
python3 src/generate_mock_data.py
```

Build or refresh the vector database:

```bash
python3 src/rag_pipeline.py
```

Run the Streamlit app:

```bash
python3 -m streamlit run src/app.py
```

Run tests:

```bash
python3 -m unittest discover tests
```
