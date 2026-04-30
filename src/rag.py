"""
RAG Engine — ChromaDB + Sentence Transformers
Indexes PDF datasheets and answers hardware safety queries.
"""

import os
import chromadb
from chromadb.utils import embedding_functions
import PyPDF2

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "datasheets"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class RAGEngine:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embed_fn,
        )

    def ingest_pdf(self, pdf_path: str, chunk_size: int = 500):
        """Parse PDF, chunk text, and store in ChromaDB."""
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"

        # Chunk by characters
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        basename = os.path.basename(pdf_path)

        ids = [f"{basename}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": basename, "chunk": i} for i in range(len(chunks))]

        # Upsert (safe for re-ingestion)
        self.collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
        print(f"[RAG] Ingested {len(chunks)} chunks from {basename}")

    def query(self, query_text: str, n_results: int = 3) -> str:
        """Query vector store and return top relevant datasheet excerpts."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        docs = results.get("documents", [[]])[0]
        if not docs:
            return ""

        # Simple post-processing: look for danger keywords
        combined = " | ".join(docs)
        return combined[:600]  # Return first 600 chars of context
