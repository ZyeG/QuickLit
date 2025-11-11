import json
import feedparser
from openai import OpenAI
import re
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

# ---------------------------------------------------------
# Setup
# ---------------------------------------------------------
load_dotenv(dotenv_path="./.env.txt")
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not found in .env.txt")

if len(sys.argv) < 2:
    print("Usage: python3 query_pipe.py \"<research topic>\" [max_results]")
    sys.exit(1)

USER_INPUT_TOPIC = sys.argv[1].strip()
MAX_RESULTS = int(sys.argv[2]) if len(sys.argv) > 2 else 20
client = OpenAI(api_key=api_key)

slug = re.sub(r"[^a-zA-Z0-9]+", "_", USER_INPUT_TOPIC.lower()).strip("_")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs("./data", exist_ok=True)
OUTPUT_PATH = f"./data/query_pipe_out_{slug}_{timestamp}.json"

# ---------------------------------------------------------
# Utility: save and read pipeline stages
# ---------------------------------------------------------
def save_stage(stage_name, content):
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data[stage_name] = content
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------
# 1️⃣ Extract Concept Clusters
# ---------------------------------------------------------
prompt_keywords = f"""
Extract the key **concept clusters** directly from this research topic (use exact words/phrases):

"{USER_INPUT_TOPIC}"

Each cluster should represent a coherent research concept
(e.g., "retrieval-augmented generation", "large language models", "education").
For each concept, list 2–3 synonyms or related expressions (including acronyms if applicable).

Output valid JSON:
[
  {{"concept": "<main phrase>", "synonyms": ["<syn1>", "<syn2>", ...]}},
  ...
]

Ensure each concept phrase is meaningful (avoid single adjectives or trivial words).
"""

resp1 = client.responses.create(
    model="gpt-4o-mini",
    input=prompt_keywords,
    temperature=0.3,
)

keywords_text = resp1.output[0].content[0].text.strip()
cleaned = re.sub(r"^```(?:json)?|```$", "", keywords_text, flags=re.MULTILINE).strip()
keywords = json.loads(cleaned)

# Filter trivial/single-word
keywords = [k for k in keywords if len(k.get("concept", "").split()) > 1]
save_stage("concept_clusters", keywords)

# ---------------------------------------------------------
# 2️⃣ Build Boolean Query
# ---------------------------------------------------------
prompt_query = f"""
You are a professional academic search-query builder.

Given these concept clusters and synonyms:
{json.dumps(keywords, indent=2)}

Return ONLY a Boolean query string (no URL encoding, no arXiv prefixes).
Rules:
- Use quotes for multi-word phrases.
- Use OR within a concept cluster.
- Use AND across at most 2–3 major clusters.
- DO NOT include 'all:' anywhere.
- DO NOT include URL encoding.

Example of the desired output shape:
("retrieval augmented generation" OR "RAG") AND ("large language models" OR "LLMs")
"""
resp2 = client.responses.create(
    model="gpt-4o-mini",
    input=prompt_query,
    temperature=0.3,
)

search_query = resp2.output[0].content[0].text.strip()
save_stage("boolean_query", search_query)

# ---------------------------------------------------------
# 3️⃣ Generate arXiv API URL
# ---------------------------------------------------------
from urllib.parse import quote_plus
import re

# sanitize the boolean query the model returned
search_query = resp2.output[0].content[0].text.strip()
# (defensive) strip any accidental leading all:(...) from the model
search_query = re.sub(r'^\s*all:\s*\((.*)\)\s*$', r'\1', search_query, flags=re.IGNORECASE)

# wrap the entire boolean logic once in all:( ...)
wrapped = f'all:({search_query})'
encoded = quote_plus(wrapped)  # encodes spaces, quotes, parentheses, etc.

api_url = f"http://export.arxiv.org/api/query?search_query={encoded}&start=0&max_results={MAX_RESULTS}"
save_stage("api_url", api_url)

# ---------------------------------------------------------
# 4️⃣ Retrieve Papers from arXiv
# ---------------------------------------------------------
feed = feedparser.parse(api_url)
papers = [
    {"title": e.title.strip(), "pdf_link": e.link.replace("/abs/", "/pdf/")}
    for e in feed.entries
]
save_stage("retrieved_papers_initial", papers)

# ---------------------------------------------------------
# 5️⃣ Fallback: Simple query with user input
# ---------------------------------------------------------
if not papers:
    print("⚠️ No papers found — retrying using user topic directly...")
    topic_encoded = re.sub(r"\s+", "%20", USER_INPUT_TOPIC.strip())
    api_url_fallback = f"http://export.arxiv.org/api/query?search_query=all:({topic_encoded})&start=0&max_results={MAX_RESULTS}"
    feed = feedparser.parse(api_url_fallback)
    papers = [
        {"title": e.title.strip(), "pdf_link": e.link.replace("/abs/", "/pdf/")}
        for e in feed.entries
    ]
    save_stage("retrieved_papers_fallback", papers)
    save_stage("api_url_fallback", api_url_fallback)
