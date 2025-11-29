from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import dotenv
from app.pdf_parser import parse_papers_to_text
dotenv.load_dotenv()
CHUNK_SIZE = 500
CHUNK_OVERLAP = 200
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)
max_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=7000,
    chunk_overlap=3500
)
# ---------------------------------------------
# RAG Pipeline Utilities
def split_text(paper):
    """
    paper: list of dict
    [{
        "title": "title",
        "pdf_url": "pdf_url",
        "paper_id": "paper_id",
        "content": "content",
        "abstract": "abstract",
    }...]
    Returns list of dicts with keys 'paper_title' and 'text' (chunk).
    """
    return_chunks = []
    for p in paper:
        chunks = text_splitter.split_text(p["content"])
        return_chunks.extend({"title": p["title"], "pdf_url": p["pdf_url"], "paper_id": p["paper_id"], "text": chunk} for chunk in chunks)
    return return_chunks

def max_split_text(paper):
    # Similar to split_text but with larger chunk size for OpenAI embeddings
    return_chunks = []
    for p in paper:
        chunks = max_text_splitter.split_text(p["content"])
        return_chunks.extend({"title": p["title"], "pdf_url": p["pdf_url"], "paper_id": p["paper_id"], "text": chunk} for chunk in chunks)
    return return_chunks
# ---------------------------------------------
from qdrant_client import QdrantClient, models
import uuid
QDRANT_CLIENT = QdrantClient(url="http://qdrant:6333")

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

def qdrant_add_openai(collection_name, data, use_max_splitter=False):
    """
    Use OpenAI embeddings instead of a local sentence-transformers model.

    data: list of dicts of papers
    """
    # parse the paper to get text content
    data, _ = parse_papers_to_text(data)
    if use_max_splitter:
        collection_name += "_8192"
    # chunk the text
    chunks = max_split_text(data) if use_max_splitter else split_text(data)
    # Compute embeddings for each document
    vectors = []
    payload = []
    ids = []
    for d in chunks:
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

def query_qdrant_openai(collection_name, query_text, top_k=5, return_points: bool = False, use_alt_collection=False):
    """
    Query Qdrant collection with input text and return top_k results.

    By default returns a formatted string for UI/debugging.
    If return_points=True, returns the raw PointStruct list for evaluation.
    """
    if use_alt_collection:
        collection_name += "_8192"
    search_result = QDRANT_CLIENT.query_points(
        collection_name=collection_name,
        query=_openai_get_embedding_vector(query_text),
        limit=top_k,
    ).points
    if return_points:
        return search_result
    return "\n".join(
        [f"Paper Title: {result.payload['title']}\nContent: {result.payload['text']}" for result in search_result]
    )

if __name__ == "__main__":
    # Example usage:
    # qdrant_add_openai(
    #     "9e958d99-36ba-415e-a9ca-38c33a4ec35c",
    #     [{
    #     "paper_id": "1506.02157",
    #     "title": "Dropout as a Bayesian Approximation: Appendix",
    #     "pdf_url": "https://arxiv.org/pdf/1506.02157.pdf",
    #     "abstract": "We show that a neural network with arbitrary depth and non-linearities, with dropout applied before every weight layer, is mathematically equivalent to an approximation to a well known Bayesian model. This interpretation might offer an explanation to some of dropout's key properties, such as its robustness to over-fitting. Our interpretation allows us to reason about uncertainty in deep learning, and allows the introduction of the Bayesian machinery into existing deep learning frameworks in a principled way.\n  This document is an appendix for the main paper \"Dropout as a Bayesian Approximation: Representing Model Uncertainty in Deep Learning\" by Gal and Ghahramani, 2015."
    #     }]
    # )

    # print(query_qdrant_openai(
    #     "9e958d99-36ba-415e-a9ca-38c33a4ec35c",
    #     "What is the Bayesian interpretation of dropout in neural networks?",
    #     top_k=3
    # ))
    pass
