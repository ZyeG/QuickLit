import json
from openai import OpenAI
import re
import os
import requests
import xml.etree.ElementTree as ET

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)


# directory of this file: backend/app/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# go up to backend/
BACKEND_DIR = os.path.dirname(BASE_DIR)
# logs directory under backend/
LOG_DIR = os.path.join(BACKEND_DIR, "log", "query_out")   # goes to backend/log/query_out/

# Max number of papers to fetch per query
MAX_PAPERS = 2

os.makedirs(LOG_DIR, exist_ok=True)

CHAT_SYSTEM_PROMPT = """You are an academic research assistant that helps to get information from researched paper.\
You will be given the context of the paper and a question related to it.\
Provide a concise and accurate answer based on the context provided.\
If the context does not contain the answer, respond with "Insufficient information."\
Do not make up answers or provide information not present in the context.\
Use formal academic language and cite specific sections or data from the paper when relevant.\
When answering, ensure clarity and coherence, making it easy for the user to understand the response.\
Avoid including any content that is not directly related to the question or context.\
Your answers should be factual and based solely on the provided context.\
Context:\n
"""

def get_arxiv_abstract(paper_id):
    url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
    resp = requests.get(url).text

    try:
        root = ET.fromstring(resp)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry = root.find("atom:entry", ns)
        abstract = entry.find("atom:summary", ns).text.strip()
        return abstract
    except Exception:
        return ""

def slugify(text):
    # keep letters and numbers, replace others with _
    s = re.sub(r"[^A-Za-z0-9]+", "_", text)
    return s.strip("_").lower()

def first10_slug(text):
    return slugify(text)[:10] or "topic"

def query(topic, model="gpt-5", out_dir=LOG_DIR):

    PROMPT = f"""
You are an academic literature search assistant.

Task:
Given the research topic: "{topic}", search ONLY on arXiv.

Requirements:
1. Retrieve papers exclusively from arXiv (no external sources).
2. Estimate the semantic similarity between the topic and each candidate title.
3. Keep only papers whose title similarity score is ≥ 0.50.
4. Return at most {str(MAX_PAPERS)} papers after filtering.
5. Prioritize:
   - high conceptual alignment
   - correct sub-domain
   - avoid unrelated general surveys
6. Every paper must be an actual arXiv entry. id, title, pdf_url triple MUST refer to the same arXiv record.

Output format:
paper_id | title | https://arxiv.org/pdf/<paper_id>.pdf

Output only the list, no commentary.
Begin now.
"""

    # Step 1: Run LLM retrieval
    response = client.responses.create(
        model=model,
        tools=[{"type": "web_search"}],
        input=PROMPT
    )

    raw_output = response.output_text

    # Step 2: Parse "id | title | url"
    papers = []
    for line in raw_output.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue

        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            continue

        paper_id, title, pdf_url = parts
        abstract = get_arxiv_abstract(paper_id)

        papers.append({
            "paper_id": paper_id,
            "title": title,
            "pdf_url": pdf_url,
            "abstract": abstract
        })

    # Step 3: REST JSON (returned to API caller)
    rest_json = {
        "num_papers": len(papers),
        "papers": papers
    }

    # Step 4: JSON log (includes topic + topic_idx)
    log_json = {
        "topic": topic,
        #"topic_idx": topic_idx,
        "num_papers": len(papers),
        "papers": papers
    }

    # Build filename from first 10 chars of topic
    fname = first10_slug(topic) + ".json"
    out_path = os.path.join(out_dir, fname)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(log_json, f, indent=2)


    return rest_json, out_path

def chat_query(query: str, context: str, model="gpt-5", stream: bool = False):
    instructions = CHAT_SYSTEM_PROMPT + context

    if stream:
        def response_generator():
            with client.responses.stream(
                model=model,
                instructions=instructions,
                input=query,
            ) as response_stream:
                for event in response_stream:
                    if event.type == "response.output_text.delta":
                        chunk = getattr(event, "delta", "")
                        if chunk:
                            yield chunk
                response_stream.get_final_response()

        return response_generator()

    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=query
    )
    return response.output_text
