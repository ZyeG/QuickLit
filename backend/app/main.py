from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import subprocess, json, os, requests, re
from app.summary import summarize_or_abstract, fetch_abstract, TimeoutException, MAX_FILE_BYTES, TIMEOUT_SECONDS
app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"message": "hello world"}

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/query")
async def run_query(request: Request):
    data = await request.json()
    topic = data.get("topic")
    max_results = str(data.get("max_results", 20))  # default = 20

    if not topic:
        return {"error": "Missing 'topic' in request body"}

    # Run pipeline with topic and max_results
    cmd = ["python3", "app/query_pipe.py", topic, max_results]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Get the newest output JSON
    out_files = sorted(
        [f for f in os.listdir("./data") if f.startswith("query_pipe_out_")],
        key=lambda f: os.path.getmtime(os.path.join("./data", f)),
        reverse=True
    )
    latest_json = os.path.join("./data", out_files[0]) if out_files else None

    if not latest_json:
        return {"error": "No output file generated"}

    with open(latest_json, "r", encoding="utf-8") as f:
        content = json.load(f)

    return {
        "topic": topic,
        "max_results": max_results,
        "pipeline_output": content,
        "stdout": result.stdout,
    }

CACHE_DIR = "./data/summaries"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_filename(pdf_url: str) -> str:
    """Turn an arXiv PDF URL into a safe filename (e.g. 2403.19889v1.json)."""
    match = re.search(r"(\d{4}\.\d{5})(v\d+)?", pdf_url)
    base = match.group(0) if match else re.sub(r"[^a-zA-Z0-9]+", "_", pdf_url)
    return os.path.join(CACHE_DIR, f"{base}.json")

# -------------------------------------------------
# Endpoint: GET /api/get_summary
# -------------------------------------------------
@app.get("/api/get_summary")
async def get_summary(url: str = Query(..., description="Direct PDF URL (e.g. https://arxiv.org/pdf/2403.19889v1)")):
    """
    Summarize a paper using GPT-4o-mini.
    - If cached: returns cached result.
    - If too long (>20 pages) or timeout (>60s): returns abstract instead.
    """
    cache_file = get_cache_filename(url)

    # Try loading from cache
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
        cached["cached"] = True
        print(f"Loaded cached summary for {url}")
        return cached

    # not cached — compute summary
    try:
        size = int(requests.head(url, timeout=10).headers.get("Content-Length", 0))
    except Exception:
        size = 0

    # Too large → abstract only
    if size > MAX_FILE_BYTES:
        abstract = fetch_abstract(url)
        result = {
            "summary": abstract,
            "type": "abstract",
            "timeout": False,
            "warning": f"File too long ({size/1024:.1f} KB > {MAX_FILE_BYTES/1024:.1f} KB), showing abstract only.",
        }
    else:
        try:
            summary_text = summarize_or_abstract(url)
            is_abstract = "Abstract not available" in summary_text or len(summary_text) < 100
            result = {
                "summary": summary_text,
                "type": "abstract" if is_abstract else "summary",
                "timeout": False,
            }
        except TimeoutException:
            abstract = fetch_abstract(url)
            result = {
                "summary": abstract,
                "type": "abstract",
                "timeout": True,
                "warning": f"Summarization timed out (> {TIMEOUT_SECONDS}s). Showing abstract instead.",
            }
        except Exception as e:
            abstract = fetch_abstract(url)
            result = {
                "summary": abstract,
                "type": "abstract",
                "timeout": False,
                "warning": f"Summarization failed ({type(e).__name__}). Showing abstract instead.",
            }

    # Save to cache
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved summary cache → {cache_file}")

    result["cached"] = False
    return result