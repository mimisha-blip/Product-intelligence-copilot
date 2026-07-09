# AI Product Intelligence Copilot

A RAG-powered product strategy assistant for roadmap decisions across customer feedback, support cases, Jira tickets, usage analytics, and competitor insights.

## What’s included

- React + Vite + TypeScript starter
- Mock SignalDesk B2B SaaS data under `data/raw/`
- CSV ingestion into LangChain-style documents
- Pinecone retrieval with local BGE embeddings
- LangGraph routing for pain points, prioritization, roadmap, and competitor questions
- Fireworks Qwen answer generation
- Streamlit portfolio UI

## Run locally

1. Install Python dependencies: `python3 -m pip install -r scripts/requirements.txt`
2. Add keys to `.env`: `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `FIREWORKS_API_KEY`, and `FIREWORKS_MODEL`
3. Generate mock data: `python3 src/generate_mock_data.py`
4. Build or refresh the vector index: `python3 src/rag_pipeline.py`
5. Start the Streamlit app: `streamlit run src/app.py`

You can also run the React starter separately:

1. Install frontend dependencies: `npm install`
2. Start dev server: `npm run dev`

## Next steps

- Replace mock CSVs with connectors to real APIs
- Store historical insight summaries and team annotations
- Add authentication and saved workspaces for team usage
