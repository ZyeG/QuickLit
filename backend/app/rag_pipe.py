from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import dotenv
dotenv.load_dotenv()
CHUNK_SIZE = 500
CHUNK_OVERLAP = 200
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)
# ---------------------------------------------
# RAG Pipeline Utilities
def split_text(paper):
    """
    paper: list of dict with key 'title' and value 'paper contents'
    Returns list of dicts with keys 'paper_title' and 'text' (chunk).
    """
    return_chunks = []
    for p in paper:
        chunks = text_splitter.split_text(p["content"])
        return_chunks.extend({"paper_title": p["title"], "text": chunk} for chunk in chunks)
    return return_chunks
# ---------------------------------------------
from qdrant_client import QdrantClient, models
import uuid
QDRANT_CLIENT = QdrantClient(url="http://localhost:6333")

# --- OpenAI-based embedding support ----------------------------------

from openai import OpenAI

# Initialize OpenAI client from environment

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"  # choose an OpenAI embedding model

def _openai_get_embedding_vector(text: str):
    """Return embedding vector (list[float]) for the input text using OpenAI."""
    # The OpenAI Python client may return nested response shapes; use output accessors accordingly
    resp = openai_client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=text)
    # resp.data[0].embedding is the usual shape
    try:
        return resp.data[0].embedding
    except Exception:
        # Fallback: if the client returns a different shape, try to access resp["data"][0]["embedding"]
        return resp["data"][0]["embedding"]

def qdrant_add_openai(collection_name, data):
    """
    Use OpenAI embeddings instead of a local sentence-transformers model.

    data: list of dicts with keys 'paper_title' and 'text'
    """
    # Compute embeddings for each document
    vectors = []
    payload = []
    ids = []
    for d in data:
        emb = _openai_get_embedding_vector(d["text"])
        vectors.append(emb)
        payload.append(d)
        ids.append(str(uuid.uuid4()))

    dim = len(vectors[0]) if vectors else 0

    # Create collection with the proper dimension if it doesn't exist
    if not QDRANT_CLIENT.collection_exists(collection_name=collection_name):
        QDRANT_CLIENT.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )

    # Upload vectors to Qdrant
    QDRANT_CLIENT.upload_collection(
        collection_name=collection_name,
        vectors=vectors,
        ids=ids,
        payload=payload,
    )

def query_qdrant_openai(collection_name, query_text, top_k=5, return_points: bool = False):
    """
    Query Qdrant collection with input text and return top_k results.

    By default returns a formatted string for UI/debugging.
    If return_points=True, returns the raw PointStruct list for evaluation.
    """
    search_result = QDRANT_CLIENT.query_points(
        collection_name=collection_name,
        query=_openai_get_embedding_vector(query_text),
        limit=top_k,
    ).points
    if return_points:
        return search_result
    return "\n".join(
        [f"Paper Title: {result.payload['paper_title']}\nContent: {result.payload['text']}" for result in search_result]
    )

if __name__ == "__main__":
    pass
