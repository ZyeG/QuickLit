from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import json, os, requests, re
from app.query_pipe import query
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

    if not topic:
        return {"error": "Missing 'topic' in request body"}

    model = data.get("model", "gpt-5")   # optional
    #out_dir = data.get("out_dir", "./log/query_out")  # optional

    rest_json, log_path = query(topic=topic, model=model)

    # return only papers (plus metadata if you want)
    return {
        "num_papers": rest_json["num_papers"],
        "papers": rest_json["papers"],
    }
 