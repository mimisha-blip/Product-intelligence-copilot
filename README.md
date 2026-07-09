# AI Product Intelligence Copilot

AI Product Intelligence Copilot is a RAG + LangGraph application that helps product managers turn scattered product signals into evidence-backed roadmap recommendations.

## Overview

Product managers often need to synthesize customer feedback, Jira tickets, support cases, usage analytics, and competitor insights before making roadmap decisions. That evidence is usually fragmented across tools, making it hard to see recurring pain points, quantify urgency, compare tradeoffs, and explain product bets clearly to leadership.

This project solves that problem with a retrieval-augmented generation workflow. It loads realistic B2B SaaS product data, embeds it with Sentence Transformers, stores it in Pinecone, retrieves relevant evidence for a product strategy question, routes the question through LangGraph, and uses Qwen on Fireworks AI to generate a structured product recommendation. A Streamlit UI makes the workflow easy to demo and explore.

## Architecture

```text
Mock Data
    ↓
Embeddings
    ↓
Pinecone
    ↓
Retriever
    ↓
LangGraph
    ↓
Fireworks AI (Qwen)
    ↓
Streamlit UI
```

The app currently uses mock SignalDesk B2B SaaS datasets across customer feedback, support, Jira, usage analytics, and competitor insights. The prioritization workflow also calculates product-area priority scores from retrieved evidence before asking the LLM to explain recommendations.

## Features

- Customer pain point analysis
- Feature prioritization
- Competitor analysis
- Q3 roadmap generation
- Evidence-backed AI recommendations
- Retrieved source display in the Streamlit UI
- Product-area scoring for prioritization questions

## Tech Stack

- Python
- LangGraph
- LangChain-style documents
- Pinecone
- Fireworks AI
- Qwen
- Sentence Transformers
- Streamlit

## Project Structure

```text
.
├── data/
│   ├── raw/                 # Mock CSV datasets
│   └── processed/           # Generated outputs, ignored by Git
├── docs/                    # Project documentation
├── src/
│   ├── app.py               # Streamlit UI
│   ├── answer_generator.py  # Fireworks/Qwen answer generation
│   ├── generate_mock_data.py
│   ├── graph.py             # LangGraph routing workflow
│   ├── ingest_data.py       # CSV-to-document ingestion
│   ├── rag_pipeline.py      # Embeddings + Pinecone retrieval
│   ├── scoring.py           # Product prioritization scoring
│   └── legacy/              # Earlier experimental scripts
├── tests/                   # Unit tests
├── .env.example             # Placeholder environment variables
├── requirements.txt         # Python dependencies
└── README.md
```

## Setup Instructions

1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Create your local environment file:

```bash
cp .env.example .env
```

3. Add your real API keys and model/index settings to `.env`:

```env
PINECONE_API_KEY=your_real_pinecone_key
PINECONE_INDEX_NAME=product-intelligence-copilot-bge
FIREWORKS_API_KEY=your_real_fireworks_key
FIREWORKS_MODEL=accounts/fireworks/models/qwen3p7-plus
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

4. Generate mock data:

```bash
python3 src/generate_mock_data.py
```

5. Build or refresh the Pinecone vector index:

```bash
python3 src/rag_pipeline.py
```

6. Start the Streamlit app:

```bash
python3 -m streamlit run src/app.py
```

7. Run tests:

```bash
python3 -m unittest discover tests
```

## Example Questions

- What are the top customer pain points?
- Which features should we prioritize?
- Generate a Q3 roadmap.
- What are competitors doing that we are not?

## Screenshots

### Streamlit Copilot UI

_Add screenshot here._

### Retrieved Evidence View

_Add screenshot here._

### Prioritization Recommendation

_Add screenshot here._

## Future Improvements

- Connect to real customer feedback, Jira, support, analytics, and competitor data sources
- Add authentication and saved workspaces for product teams
- Add richer priority scoring with configurable weights
- Store generated recommendations and evidence snapshots
- Add evaluation tests for retrieval quality and answer grounding
- Deploy the Streamlit app for public portfolio demos

## Security Notes

Secrets should live only in `.env`. The repository includes `.env.example` with placeholders, and `.env` is ignored by Git.
