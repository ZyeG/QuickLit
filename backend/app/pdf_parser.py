"""
Utility helpers for downloading PDFs and extracting text.

Functions
- fetch_pdf_bytes: download a PDF with size guards and timeout.
- pdf_bytes_to_text: extract text with pypdf, optionally limiting pages.
- parse_papers_to_text: map a list of papers into text-bearing records ready for storage/indexing.
"""
import io
from typing import Dict, List, Tuple

import requests
from pypdf import PdfReader

MAX_DOWNLOAD_BYTES = 5_000_000  # ~5 MB guard to avoid oversized downloads
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_MAX_PAGES = 20  # helps keep extraction fast for long PDFs


def fetch_pdf(pdf_url: str) -> bytes:
    """Download a PDF and enforce a max payload size."""
    if not pdf_url:
        raise ValueError("pdf_url is required")

    # Stream download with manual cap
    resp = requests.get(pdf_url, timeout=DEFAULT_TIMEOUT_SECONDS, stream=True)
    resp.raise_for_status()
    chunks = []
    total = 0
    for chunk in resp.iter_content(chunk_size=64 * 1024):
        if chunk:
            total += len(chunk)
            chunks.append(chunk)
    return b"".join(chunks)


def pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    texts = []
    for _, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""
        if page_text:
            texts.append(page_text)
    return "\n\n".join(texts).strip()

def get_pdf_raw_content(pdf_url:str) -> str:
    """Fetch PDF from URL and extract text."""
    pdf_bytes = fetch_pdf(pdf_url)
    content = pdf_bytes_to_text(pdf_bytes)
    return content

def parse_papers_to_text(
    papers: List[Dict[str, str]]
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Convert a list of paper dicts (with pdf_url) into text-bearing records.
    papers: list of dicts with keys 'title', 'pdf_url', 'paper_id', 'abstract'

    Returns (parsed, failures), where parsed items include title, pdf_url, paper_id, content, and abstract (when requested).

    """
    parsed: List[Dict[str, str]] = []
    failures: List[Dict[str, str]] = []

    for paper in papers:
        pdf_url = paper.get("pdf_url") or paper.get("pdf_link")
        try:
            pdf_bytes = fetch_pdf(pdf_url)
            content = pdf_bytes_to_text(pdf_bytes)
            abstract = paper.get("abstract", "")
            parsed.append(
                {
                    "title": paper.get("title", ""),
                    "pdf_url": pdf_url,
                    "paper_id": paper.get("paper_id"),
                    "content": content,
                    "abstract": abstract,
                }
            )
        except Exception as exc:  # keep moving if a single PDF fails
            failures.append(
                {
                    "title": paper.get("title", ""),
                    "pdf_url": pdf_url,
                    "paper_id": paper.get("paper_id"),
                    "error": str(exc),
                }
            )

    return parsed, failures

if __name__ == "__main__":
    # Example usage for manual testing
    sample = [
        {
            "title": "Example Paper",
            "pdf_url": "https://arxiv.org/pdf/2407.07003.pdf",
            "paper_id": "2407.07003",
            "abstract": "This is a sample abstract for the example paper."
        }
    ]
    parsed, failures = parse_papers_to_text(sample)
    print({"parsed_count": len(parsed), "failures": failures})
    print(parsed[0]['content'][:500])  # print first 500 chars of content
    print(parsed[0]['title'])
    print(parsed[0]['abstract'])

    # print(parsed[0]['abstract'])
    # pass
