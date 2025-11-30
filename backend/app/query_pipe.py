import json
from openai import OpenAI
import re
import os
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import html
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)


# directory of this file: backend/app/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# go up to backend/
BACKEND_DIR = os.path.dirname(BASE_DIR)
# logs directory under backend/
LOG_DIR = os.path.join(BACKEND_DIR, "log", "query_out")   # goes to backend/log/query_out/
SUMMARIES_LOG_DIR = os.path.join(BACKEND_DIR, "log", "summaries")   # goes to backend/log/summaries/
# Max number of papers to fetch per query
MAX_PAPERS = 30

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SUMMARIES_LOG_DIR, exist_ok=True)
CHAT_SYSTEM_PROMPT = """
You are an academic research assistant that helps to get information from researched paper.\
You will be given the context of the paper and a question related to it.\
Provide a concise and accurate answer based on the context provided.\
If the context does not contain the answer, respond with "Insufficient information."\
Do not make up answers or provide information not present in the context.\
Use formal academic language and cite specific sections or data from the paper when relevant.\
When answering, ensure clarity and coherence, making it easy for the user to understand the response.\
Avoid including any content that is not directly related to the question or context.\
Your answers should be factual and based solely on the provided context.\
First give a brief answer, then provide detailed explanation.\
Context:\n
"""
def get_arxiv_abstract(paper_id: str) -> str:
    url = f"https://arxiv.org/abs/{paper_id}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    meta = soup.find("meta", attrs={"name": "citation_abstract"}) \
        or soup.find("meta", attrs={"property": "og:description"})

    content = meta.get("content", "") if meta else ""
    # Normalize whitespace and unescape HTML entities.
    abstract = " ".join(content.split())
    return html.unescape(abstract)

def slugify(text):
    # keep letters and numbers, replace others with _
    s = re.sub(r"[^A-Za-z0-9]+", "_", text)
    return s.strip("_").lower()

def first10_slug(text):
    return slugify(text)[:10] or "topic"

def query(topic, model="gpt-5", out_dir=LOG_DIR):

    # PROMPT = f"""
    # You are an academic literature search assistant.

    # Task:
    # Given the research topic: "{topic}", search ONLY on arXiv.

    # Requirements:
    # 1. Retrieve papers exclusively from arXiv (no external sources).
    # 2. Estimate the semantic similarity between the topic and each candidate title.
    # 3. Keep only papers whose title similarity score is ≥ 0.50.
    # 4. Return at most {str(MAX_PAPERS)} papers after filtering.
    # 5. Prioritize:
    #    - high conceptual alignment
    #    - correct sub-domain
    #    - avoid unrelated general surveys
    # 6. Every paper must be an actual arXiv entry. id, title, pdf_url triple MUST refer to the same arXiv record.

    # Output format:
    # paper_id | title | https://arxiv.org/pdf/<paper_id>.pdf

    # Output only the list, no commentary.
    # Begin now.
    # """

    PROMPT = f"""You are an academic literature search assistant.

    ====================================================
    INTERNAL STEP 1 — EXTRACT CONCEPT CLUSTERS
    ====================================================
    Given the research topic: "{topic}"

    Extract 3-5 tightly relevant, non-overlapping concept clusters.
    Rules:
    - Avoid splitting the topic into too many parts.
    - Each concept should increase retrieval precision, not widen scope.
    - Include synonyms only if they correspond to actual terminology in arXiv papers.

    ====================================================
    INTERNAL STEP 2 — BUILD SEARCH QUERIES
    ====================================================
    Using the concept clusters:
    - Construct 5-8 weighted search queries.
    - Use OR within concept groups.
    - Combine groups softly (not strict AND), so retrieval is flexible but still precise.

    ====================================================
    INTERNAL STEP 3 — ARXIV-ONLY RETRIEVAL
    ====================================================
    Search **exclusively on arXiv**.
    Retrieve candidate papers with:
    - paper_id
    - title
    - pdf_url (e.g. https://arxiv.org/pdf/<paper_id>.pdf)

    No external sources allowed.

    ====================================================
    INTERNAL STEP 4 — SEMANTIC SCORING & FILTERING
    ====================================================
    For every candidate paper:
    - Estimate title-topic semantic similarity.
    - Keep only papers with similarity ≥ 0.50.
    - Enforce that id, title, and pdf_url all correspond to the same real arXiv record.
    - After filtering, keep at most {str(MAX_PAPERS)} papers.
    - Prioritize:
    * high conceptual alignment
    * correct sub-domain
    * avoid unrelated, too general overviews, or too narrow papers.

    ====================================================
    INTERNAL STEP 5 — RANK & PREPARE OUTPUT
    ====================================================
    Rank remaining papers by:
    - semantic relevance
    - conceptual tightness
    - closeness to the topic (not popularity)

    Format each output line as:
    paper_id | title | https://arxiv.org/pdf/<paper_id>.pdf

    ====================================================
    FINAL OUTPUT (VISIBLE TO USER)
    ====================================================
    Output ONLY the final list of formatted lines.
    Do NOT reveal internal steps or reasoning.
    Do NOT add commentary.
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

# get_summary: intake arxiv id, output summary text
def get_summary(id, model="gpt-5"):
    pdf_url = f"https://arxiv.org/pdf/{id}.pdf"
    PROMPT = f"""
    You are an academic research assistant.
    Read the paper at {pdf_url} and identify all first level sections (Methods, Results, Discussion, etc.), and provide a concise summary of each section (1-2 sentences for shorter sections, 3-4 sentences for longer sections).

    Do not summarize Abstract, Acknowledgements or References.

    Output format:
    <paper title>
    <section 1 title>:<section 1 summary>

    <section 2 title>:<section 2 summary>

    <section N title>:<section N summary>
    ...

    Do not include citations or urls in the output. 
    """

    response = client.responses.create(
        model=model,
        input=PROMPT,
        tools=[{"type": "web_search"}],
    )

    summary = response.output_text.strip()
    return summary
