from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
from app.query_pipe import query, chat_query
from app.rag_pipe import qdrant_add_openai, query_qdrant_openai
import json
app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# go up to backend/
BACKEND_DIR = os.path.dirname(BASE_DIR)
# logs directory under backend/
LOG_DIR = os.path.join(BACKEND_DIR, "log", "query_out")   # goes to backend/log/query_out/

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

    # debug print
    print(f"Running query for topic: {topic}", flush=True)


    if not topic:
        return {"error": "Missing 'topic' in request body"}

    model = data.get("model", "gpt-5")   # optional
    #out_dir = data.get("out_dir", "./log/query_out")  # optional

    topic_lower = topic.strip().lower()

    # scan all .json files in LOG_DIR to see if we have cached result
    for fname in os.listdir(LOG_DIR):
        # debug print file name
        print(f"Checking cache file: {fname}", flush=True)

        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(LOG_DIR, fname)
        try:
            with open(fpath, "r") as f:
                cached_data = json.load(f)
            cached_topic = cached_data.get("topic", "").strip().lower()
            if cached_topic == topic_lower:
                # cache hit
                print(f"Cache hit for topic: {topic}", flush=True)
                return {
                    "num_papers": cached_data.get("num_papers", 0),
                    "papers": cached_data.get("papers", []),
                }
        except Exception:
            print(f"Skipping invalid JSON file: {fpath}", flush=True)
            # debug print exception
            traceback.print_exc()
            continue   # skip invalid json files
    # cache miss, run query
    rest_json, _ = query(topic=topic, model=model)

    # return only papers (plus metadata if you want)
    return {
        "num_papers": rest_json["num_papers"],
        "papers": rest_json["papers"],
    }
 
#  Endpoint to add papers to a Qdrant collection
@app.post("/api/collections/papers/add")
async def add_papers(request: Request):
    data = await request.json()
    session = data.get("session")
    collection_name = session['id']
    papers = session['papers']

    if not collection_name or not papers:
        return {"error": "Missing 'collection_name' or 'papers' in request body"}, 400

    # Here you would call your function to add papers to the collection
    qdrant_add_openai(collection_name, papers)
    return {"status": "success", "message": f"Added {len(papers)} papers to collection '{collection_name}'"}

#  Endpoint to query papers from a Qdrant collection
@app.post("/api/collections/papers/query")
async def query_collection(request: Request):
    data = await request.json()
    collection_name = data.get('collection_name')
    query_text = data.get('query_text')
    top_k = data.get('top_k', 10)

    if not collection_name or not query_text:
        return {"error": "Missing 'collection_name' or 'query_text' in query parameters"}

    results = query_qdrant_openai(
        collection_name=collection_name,
        query_text=query_text,
        top_k=top_k,
    )

    return results

@app.post("/api/chat/stream")
async def generate_stream(request: Request):
    data = await request.json()
    print(data)
    collection_name = data.get("collection_name")
    query_text = data.get("query_text")

    if not collection_name:
        return {"error": "Missing 'collection_name' in request body"}
    if not query_text:
        return {"error": "Missing 'query_text' in request body"}
    results = query_qdrant_openai(
                collection_name=collection_name,
                query_text=query_text,
                top_k=10,
                )

    response_stream = chat_query(query=query_text, context=results, model="gpt-5", stream=True)

    return StreamingResponse(response_stream, media_type="text/plain")
