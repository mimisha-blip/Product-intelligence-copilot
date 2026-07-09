import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "rag_pipeline.py"


class FakeDocument:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


class FakeEmbeddingArray:
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return self.values


class FakeSentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name
        self.encode_calls = []

    def encode(self, texts, normalize_embeddings=True, show_progress_bar=False):
        self.encode_calls.append({
            "texts": texts,
            "normalize_embeddings": normalize_embeddings,
            "show_progress_bar": show_progress_bar,
        })
        return [FakeEmbeddingArray([float(index)] * 384) for index, _text in enumerate(texts, start=1)]


class FakeIndex:
    def __init__(self):
        self.upsert_calls = []
        self.query_calls = []

    def upsert(self, vectors):
        self.upsert_calls.append(vectors)

    def query(self, vector, top_k, include_metadata):
        self.query_calls.append({
            "vector": vector,
            "top_k": top_k,
            "include_metadata": include_metadata,
        })
        return {
            "matches": [
                {
                    "score": 0.88,
                    "metadata": {
                        "text": "A reporting issue is affecting enterprise accounts.",
                        "source_type": "customer_feedback",
                        "product_area": "Reporting",
                        "severity": "High",
                    },
                }
            ]
        }


class FakePinecone:
    def __init__(self, api_key, existing_indexes=None):
        self.api_key = api_key
        self.existing_indexes = existing_indexes or []
        self.created_indexes = []
        self.index = FakeIndex()

    def list_indexes(self):
        return self.existing_indexes

    def create_index(self, name, dimension, metric, spec):
        self.created_indexes.append({
            "name": name,
            "dimension": dimension,
            "metric": metric,
            "spec": spec,
        })

    def Index(self, name):
        self.index_name = name
        return self.index


class RagPipelineTest(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("rag_pipeline", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_build_vector_db_uses_bge_embeddings_and_configured_pinecone_index(self):
        module = self.load_module()
        fake_pinecone = FakePinecone("pinecone-key")
        documents = [
            FakeDocument(
                "Reporting exports timeout for enterprise customers.",
                {
                    "source_type": "customer_feedback",
                    "product_area": "Reporting",
                    "severity": "High",
                    "date": "2026-01-12",
                    "id": "CF-0001",
                },
            )
        ]

        with patch.dict(os.environ, {"PINECONE_API_KEY": "pinecone-key", "PINECONE_INDEX_NAME": "test-index"}):
            with patch.object(module, "Pinecone", return_value=fake_pinecone):
                with patch.object(module, "SentenceTransformer", FakeSentenceTransformer):
                    index = module.build_vector_db(documents=documents, batch_size=10)

        self.assertIs(index, fake_pinecone.index)
        self.assertEqual("test-index", fake_pinecone.created_indexes[0]["name"])
        self.assertEqual(384, fake_pinecone.created_indexes[0]["dimension"])
        self.assertEqual("cosine", fake_pinecone.created_indexes[0]["metric"])
        self.assertEqual("test-index", fake_pinecone.index_name)
        upserted = fake_pinecone.index.upsert_calls[0][0]
        self.assertEqual("customer_feedback-CF-0001", upserted["id"])
        self.assertEqual([1.0] * 384, upserted["values"])
        self.assertEqual("Reporting exports timeout for enterprise customers.", upserted["metadata"]["text"])
        self.assertEqual("Reporting", upserted["metadata"]["product_area"])

    def test_get_retriever_queries_pinecone_with_local_query_embedding(self):
        module = self.load_module()
        fake_pinecone = FakePinecone("pinecone-key")

        with patch.dict(os.environ, {"PINECONE_API_KEY": "pinecone-key", "PINECONE_INDEX_NAME": "test-index"}):
            with patch.object(module, "Pinecone", return_value=fake_pinecone):
                with patch.object(module, "SentenceTransformer", FakeSentenceTransformer):
                    retriever = module.get_retriever(k=5)
                    matches = retriever("What reporting issues affect enterprise accounts?")

        self.assertEqual(5, fake_pinecone.index.query_calls[0]["top_k"])
        self.assertTrue(fake_pinecone.index.query_calls[0]["include_metadata"])
        self.assertEqual([1.0] * 384, fake_pinecone.index.query_calls[0]["vector"])
        self.assertEqual("customer_feedback", matches[0]["metadata"]["source_type"])

    def test_existing_index_with_wrong_dimension_raises_clear_error(self):
        module = self.load_module()
        existing_index = type("IndexInfo", (), {"name": "test-index", "dimension": 1536})()
        fake_pinecone = FakePinecone("pinecone-key", existing_indexes=[existing_index])

        with patch.dict(os.environ, {"PINECONE_API_KEY": "pinecone-key", "PINECONE_INDEX_NAME": "test-index"}):
            with patch.object(module, "Pinecone", return_value=fake_pinecone):
                with self.assertRaisesRegex(RuntimeError, "dimension 1536"):
                    module.build_vector_db(documents=[], batch_size=10)


if __name__ == "__main__":
    unittest.main()
