from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import subprocess, json, os

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

    # Run your existing pipeline as a subprocess
    cmd = ["python3", "app/query_pipe.py", topic]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Find most recent JSON output
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

    return {"topic": topic, "pipeline_output": content, "stdout": result.stdout}