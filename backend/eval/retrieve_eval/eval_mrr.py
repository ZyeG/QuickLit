"""
Evaluation helper for query_qdrant_openai using MRR.

Steps:
- Downloads and parses three sample arXiv papers.
- Chunks them, stores in Qdrant, and runs queries.
- Computes Mean Reciprocal Rank to ensure each paper is retrieved in the top-k.
"""
import os
import sys
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.pdf_parser import parse_papers_to_text
from app.rag_pipe import (
    QDRANT_CLIENT,
    split_text,
    qdrant_add_openai,
    query_qdrant_openai,
)


SAMPLE_ABS_URLS = [
    "https://arxiv.org/abs/2511.04213",
    "https://arxiv.org/abs/2511.01956",
    "https://arxiv.org/abs/2511.03070",
]


def to_pdf_url(abs_url: str) -> str:
    # arXiv PDF links: replace /abs/ with /pdf/ and append .pdf when missing
    pdf_url = abs_url.replace("/abs/", "/pdf/")
    if not pdf_url.endswith(".pdf"):
        pdf_url += ".pdf"
    return pdf_url


def prepare_papers(abs_urls: List[str]) -> List[Dict[str, str]]:
    papers = []
    for abs_url in abs_urls:
        paper_id = abs_url.rstrip("/").split("/")[-1]
        title = fetch_title_from_abs(abs_url) or paper_id  # fallback if parsing fails
        papers.append(
            {
                "title": title,
                "paper_id": paper_id,
                "pdf_url": to_pdf_url(abs_url),
            }
        )
    return papers


def fetch_title_from_abs(abs_url: str) -> str:
    """Fetch the paper title from an arXiv abs page."""
    try:
        html = requests.get(abs_url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        h1 = soup.find("h1", {"class": lambda c: c and "title" in c})
        if h1:
            # h1 text is usually "Title: <actual title>"
            text = h1.get_text(strip=True)
            return text.replace("Title:", "").strip() or text
    except Exception:
        pass
    return ""


def reciprocal_rank(points, target_title: str) -> float:
    for idx, pt in enumerate(points):
        if pt.payload.get("paper_title") == target_title:
            return 1.0 / (idx + 1)
    return 0.0


def run_mrr_evaluation(top_k: int = 10) -> None:
    collection_name = "eval_mrr_openai"

    # Start fresh
    # if QDRANT_CLIENT.collection_exists(collection_name=collection_name):
    #     QDRANT_CLIENT.delete_collection(collection_name=collection_name)

    # Prepare and parse papers (fetches PDFs, extracts content + abstract)
    papers = prepare_papers(SAMPLE_ABS_URLS)
    parsed, failures = parse_papers_to_text(papers)
    if failures:
        print("Failed to parse some papers:", failures)
    if not parsed:
        raise RuntimeError("No papers parsed; cannot proceed with evaluation.")

    # Chunk and ingest into Qdrant
    chunk_input = [{"title": p["title"], "content": p["content"]} for p in parsed]
    # Commented out to avoid re-adding on every run
    # chunks = split_text(chunk_input)
    # qdrant_add_openai(collection_name, chunks)

    # Build multiple query variants per paper to probe ranking quality
    queries = []
    for p in parsed:
        queries.extend(
            [
                {"query": f"summary of paper '{p['title']}'", "target_title": p["title"]},
                {"query": f"what are the key contributions of '{p['title']}'", "target_title": p["title"]},
                {"query": f"methods used in '{p['title']}'", "target_title": p["title"]},
                {"query": f"which problem does '{p['title']}' address", "target_title": p["title"]},
            ]
        )

    # Compute reciprocal ranks
    rrs = []
    for q in queries:
        points = query_qdrant_openai(
            collection_name, q["query"], top_k=top_k, return_points=True
        )
        rr = reciprocal_rank(points, q["target_title"])
        rrs.append(rr)
        print(f"Query: {q['query']!r} | RR: {rr:.3f}")

    mrr = sum(rrs) / len(rrs) if rrs else 0.0
    print(f"\nMRR@{top_k}: {mrr:.3f}")


if __name__ == "__main__":
    run_mrr_evaluation(top_k=10)
